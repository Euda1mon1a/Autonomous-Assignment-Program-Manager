"""Tests for the retry decorator and executor error paths.

Covers:
- RetryConfig validation (invalid max_attempts, base_delay, etc.)
- RetryExecutor.should_retry logic
- RetryExecutor.execute_sync success and failure paths
- RetryExecutor.execute_async success and failure paths
- MaxRetriesExceeded error with correct attributes
- NonRetryableError for excluded exceptions
- RetryTimeoutError when overall timeout exceeded
- Callback invocations (on_retry, on_success, on_failure)
- @retry decorator for sync and async functions
- Backoff strategies and jitter types
"""

import asyncio
import time
from unittest.mock import MagicMock

import pytest

from app.resilience.retry.context import RetryAttempt, RetryContext
from app.resilience.retry.decorator import RetryConfig, RetryExecutor, retry
from app.resilience.retry.exceptions import (
    InvalidRetryConfigError,
    MaxRetriesExceeded,
    NonRetryableError,
    RetryTimeoutError,
)
from app.resilience.retry.jitter import (
    DecorrelatedJitter,
    EqualJitter,
    FullJitter,
    JitterType,
    NoJitter,
    get_jitter_strategy,
)
from app.resilience.retry.strategies import (
    BackoffStrategy,
    ExponentialBackoffStrategy,
    ExponentialBackoffWithCeiling,
    FixedDelayStrategy,
    LinearBackoffStrategy,
    get_retry_strategy,
)


# ---------------------------------------------------------------------------
# RetryConfig validation
# ---------------------------------------------------------------------------


class TestRetryConfigValidation:
    """Tests for RetryConfig constructor validation."""

    def test_valid_config(self):
        """Valid config initializes without error."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=60.0,
            multiplier=2.0,
        )
        assert config.max_attempts == 3

    def test_max_attempts_zero_raises(self):
        """max_attempts < 1 raises InvalidRetryConfigError."""
        with pytest.raises(InvalidRetryConfigError) as exc_info:
            RetryConfig(max_attempts=0)
        assert exc_info.value.config_field == "max_attempts"

    def test_negative_base_delay_raises(self):
        """Negative base_delay raises InvalidRetryConfigError."""
        with pytest.raises(InvalidRetryConfigError) as exc_info:
            RetryConfig(base_delay=-1.0)
        assert exc_info.value.config_field == "base_delay"

    def test_max_delay_less_than_base_raises(self):
        """max_delay < base_delay raises InvalidRetryConfigError."""
        with pytest.raises(InvalidRetryConfigError) as exc_info:
            RetryConfig(base_delay=5.0, max_delay=1.0)
        assert exc_info.value.config_field == "max_delay"

    def test_multiplier_less_than_one_raises(self):
        """multiplier < 1 raises InvalidRetryConfigError."""
        with pytest.raises(InvalidRetryConfigError) as exc_info:
            RetryConfig(multiplier=0.5)
        assert exc_info.value.config_field == "multiplier"

    def test_negative_timeout_raises(self):
        """Negative timeout raises InvalidRetryConfigError."""
        with pytest.raises(InvalidRetryConfigError) as exc_info:
            RetryConfig(timeout=-1.0)
        assert exc_info.value.config_field == "timeout"

    def test_zero_timeout_raises(self):
        """Zero timeout raises InvalidRetryConfigError."""
        with pytest.raises(InvalidRetryConfigError) as exc_info:
            RetryConfig(timeout=0.0)
        assert exc_info.value.config_field == "timeout"


# ---------------------------------------------------------------------------
# RetryExecutor.should_retry
# ---------------------------------------------------------------------------


class TestRetryExecutorShouldRetry:
    """Tests for RetryExecutor.should_retry logic."""

    def test_retryable_exception_returns_true(self):
        """Retryable exception returns True."""
        config = RetryConfig(retryable_exceptions=(ConnectionError,))
        executor = RetryExecutor(config)
        assert executor.should_retry(ConnectionError()) is True

    def test_non_retryable_exception_returns_false(self):
        """Non-retryable exception returns False even if it matches retryable."""
        config = RetryConfig(
            retryable_exceptions=(Exception,),
            non_retryable_exceptions=(ValueError,),
        )
        executor = RetryExecutor(config)
        assert executor.should_retry(ValueError("bad")) is False

    def test_unmatched_exception_returns_false(self):
        """Exception not in retryable list returns False."""
        config = RetryConfig(retryable_exceptions=(IOError,))
        executor = RetryExecutor(config)
        assert executor.should_retry(ValueError("bad")) is False


# ---------------------------------------------------------------------------
# RetryExecutor.execute_sync
# ---------------------------------------------------------------------------


class TestRetryExecutorSync:
    """Tests for synchronous retry execution."""

    def test_success_on_first_attempt(self):
        """Successful first attempt returns result immediately."""
        config = RetryConfig(max_attempts=3, base_delay=0.01, jitter=JitterType.NONE)
        executor = RetryExecutor(config)

        result = executor.execute_sync(lambda: 42)
        assert result == 42

    def test_success_on_second_attempt(self):
        """Retries once and succeeds on second attempt."""
        config = RetryConfig(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        executor = RetryExecutor(config)

        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "success"

        result = executor.execute_sync(flaky)
        assert result == "success"
        assert call_count == 2

    def test_all_attempts_exhausted(self):
        """MaxRetriesExceeded raised when all attempts fail."""
        config = RetryConfig(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        executor = RetryExecutor(config)

        def always_fail():
            raise ConnectionError("fail")

        with pytest.raises(MaxRetriesExceeded) as exc_info:
            executor.execute_sync(always_fail)

        assert exc_info.value.attempts == 3
        assert exc_info.value.operation == "always_fail"
        assert isinstance(exc_info.value.last_exception, ConnectionError)

    def test_non_retryable_exception_stops_immediately(self):
        """NonRetryableError raised immediately for non-retryable exceptions."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.001,
            jitter=JitterType.NONE,
            non_retryable_exceptions=(ValueError,),
        )
        executor = RetryExecutor(config)

        call_count = 0

        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad input")

        with pytest.raises(NonRetryableError):
            executor.execute_sync(raises_value_error)

        assert call_count == 1  # Only called once, no retry

    def test_on_success_callback(self):
        """on_success callback is invoked on success."""
        callback = MagicMock()
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.001,
            jitter=JitterType.NONE,
            on_success=callback,
        )
        executor = RetryExecutor(config)

        executor.execute_sync(lambda: 42)
        callback.assert_called_once()

    def test_on_failure_callback(self):
        """on_failure callback is invoked when all retries exhausted."""
        callback = MagicMock()
        config = RetryConfig(
            max_attempts=2,
            base_delay=0.001,
            jitter=JitterType.NONE,
            on_failure=callback,
        )
        executor = RetryExecutor(config)

        with pytest.raises(MaxRetriesExceeded):
            executor.execute_sync(lambda: (_ for _ in ()).throw(OSError("fail")))

        callback.assert_called_once()

    def test_on_retry_callback(self):
        """on_retry callback is invoked before each retry."""
        callback = MagicMock()
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.001,
            jitter=JitterType.NONE,
            on_retry=callback,
        )
        executor = RetryExecutor(config)

        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("transient")
            return "ok"

        executor.execute_sync(flaky)
        # on_retry called before attempts 2 and 3
        assert callback.call_count == 2


# ---------------------------------------------------------------------------
# RetryExecutor.execute_async
# ---------------------------------------------------------------------------


class TestRetryExecutorAsync:
    """Tests for asynchronous retry execution."""

    @pytest.mark.asyncio
    async def test_async_success_first_attempt(self):
        """Async success on first attempt returns immediately."""
        config = RetryConfig(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        executor = RetryExecutor(config)

        async def success():
            return "async_ok"

        result = await executor.execute_async(success)
        assert result == "async_ok"

    @pytest.mark.asyncio
    async def test_async_retries_on_failure(self):
        """Async function retries on transient failure."""
        config = RetryConfig(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        executor = RetryExecutor(config)

        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "recovered"

        result = await executor.execute_async(flaky)
        assert result == "recovered"

    @pytest.mark.asyncio
    async def test_async_max_retries_exceeded(self):
        """Async raises MaxRetriesExceeded after all attempts."""
        config = RetryConfig(max_attempts=2, base_delay=0.001, jitter=JitterType.NONE)
        executor = RetryExecutor(config)

        async def always_fail():
            raise OSError("fail")

        with pytest.raises(MaxRetriesExceeded):
            await executor.execute_async(always_fail)

    @pytest.mark.asyncio
    async def test_async_non_retryable(self):
        """Async non-retryable exception stops immediately."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.001,
            jitter=JitterType.NONE,
            non_retryable_exceptions=(TypeError,),
        )
        executor = RetryExecutor(config)

        async def raises_type_error():
            raise TypeError("bad")

        with pytest.raises(NonRetryableError):
            await executor.execute_async(raises_type_error)


# ---------------------------------------------------------------------------
# @retry decorator
# ---------------------------------------------------------------------------


class TestRetryDecorator:
    """Tests for the @retry decorator."""

    def test_sync_decorator_success(self):
        """Sync function decorated with @retry succeeds normally."""

        @retry(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        def sync_fn():
            return "decorated"

        assert sync_fn() == "decorated"

    def test_sync_decorator_retries(self):
        """Sync function with @retry retries on failure."""
        call_count = 0

        @retry(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_decorator_success(self):
        """Async function decorated with @retry succeeds normally."""

        @retry(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        async def async_fn():
            return "async_decorated"

        result = await async_fn()
        assert result == "async_decorated"

    @pytest.mark.asyncio
    async def test_async_decorator_retries(self):
        """Async function with @retry retries on failure."""
        call_count = 0

        @retry(max_attempts=3, base_delay=0.001, jitter=JitterType.NONE)
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "recovered"

        result = await flaky()
        assert result == "recovered"


# ---------------------------------------------------------------------------
# Backoff strategies
# ---------------------------------------------------------------------------


class TestBackoffStrategies:
    """Tests for retry backoff strategies."""

    def test_fixed_delay(self):
        """Fixed strategy always returns the same delay."""
        strategy = FixedDelayStrategy(delay=2.0)
        assert strategy.calculate_delay(0) == 2.0
        assert strategy.calculate_delay(5) == 2.0
        assert strategy.calculate_delay(100) == 2.0

    def test_linear_backoff(self):
        """Linear strategy increases linearly."""
        strategy = LinearBackoffStrategy(base_delay=1.0, increment=2.0)
        assert strategy.calculate_delay(0) == 1.0
        assert strategy.calculate_delay(1) == 3.0
        assert strategy.calculate_delay(2) == 5.0

    def test_exponential_backoff(self):
        """Exponential strategy doubles each attempt."""
        strategy = ExponentialBackoffStrategy(base_delay=1.0, multiplier=2.0)
        assert strategy.calculate_delay(0) == 1.0
        assert strategy.calculate_delay(1) == 2.0
        assert strategy.calculate_delay(2) == 4.0
        assert strategy.calculate_delay(3) == 8.0

    def test_exponential_with_ceiling(self):
        """Exponential with ceiling caps at max_delay."""
        strategy = ExponentialBackoffWithCeiling(
            base_delay=1.0, multiplier=2.0, max_delay=5.0
        )
        # get_delay applies the cap
        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 2.0
        assert strategy.get_delay(2) == 4.0
        assert strategy.get_delay(3) == 5.0  # capped
        assert strategy.get_delay(10) == 5.0  # still capped

    def test_get_retry_strategy_fixed(self):
        """Factory returns FixedDelayStrategy for FIXED."""
        strategy = get_retry_strategy(BackoffStrategy.FIXED, base_delay=3.0)
        assert isinstance(strategy, FixedDelayStrategy)

    def test_get_retry_strategy_linear(self):
        """Factory returns LinearBackoffStrategy for LINEAR."""
        strategy = get_retry_strategy(BackoffStrategy.LINEAR, base_delay=1.0)
        assert isinstance(strategy, LinearBackoffStrategy)

    def test_get_retry_strategy_exponential_no_cap(self):
        """Factory returns ExponentialBackoffStrategy without max_delay."""
        strategy = get_retry_strategy(
            BackoffStrategy.EXPONENTIAL, base_delay=1.0, max_delay=None
        )
        assert isinstance(strategy, ExponentialBackoffStrategy)

    def test_get_retry_strategy_exponential_with_cap(self):
        """Factory returns ExponentialBackoffWithCeiling with max_delay."""
        strategy = get_retry_strategy(
            BackoffStrategy.EXPONENTIAL, base_delay=1.0, max_delay=30.0
        )
        assert isinstance(strategy, ExponentialBackoffWithCeiling)

    def test_unknown_strategy_raises(self):
        """Unknown strategy raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backoff strategy"):
            get_retry_strategy("not_a_strategy", base_delay=1.0)


# ---------------------------------------------------------------------------
# Jitter strategies
# ---------------------------------------------------------------------------


class TestJitterStrategies:
    """Tests for retry jitter strategies."""

    def test_no_jitter(self):
        """NoJitter returns delay unchanged."""
        jitter = NoJitter()
        assert jitter.apply(5.0, attempt=0) == 5.0

    def test_full_jitter_range(self):
        """FullJitter returns value between 0 and delay."""
        jitter = FullJitter()
        for _ in range(100):
            result = jitter.apply(10.0, attempt=0)
            assert 0 <= result <= 10.0

    def test_equal_jitter_range(self):
        """EqualJitter returns value between delay/2 and delay."""
        jitter = EqualJitter()
        for _ in range(100):
            result = jitter.apply(10.0, attempt=0)
            assert 5.0 <= result <= 10.0

    def test_decorrelated_jitter_first_attempt(self):
        """DecorrelatedJitter first attempt uses base_delay to delay range."""
        jitter = DecorrelatedJitter(base_delay=1.0)
        for _ in range(100):
            result = jitter.apply(5.0, attempt=0, previous_delay=0.0)
            assert 1.0 <= result <= 5.0

    def test_decorrelated_jitter_subsequent(self):
        """DecorrelatedJitter subsequent attempts use previous_delay * 3."""
        jitter = DecorrelatedJitter(base_delay=1.0)
        for _ in range(100):
            result = jitter.apply(5.0, attempt=1, previous_delay=2.0)
            assert 1.0 <= result <= 6.0  # base_delay to previous * 3

    def test_get_jitter_strategy_none(self):
        """Factory returns NoJitter for NONE."""
        assert isinstance(get_jitter_strategy(JitterType.NONE), NoJitter)

    def test_get_jitter_strategy_full(self):
        """Factory returns FullJitter for FULL."""
        assert isinstance(get_jitter_strategy(JitterType.FULL), FullJitter)

    def test_get_jitter_strategy_equal(self):
        """Factory returns EqualJitter for EQUAL."""
        assert isinstance(get_jitter_strategy(JitterType.EQUAL), EqualJitter)

    def test_get_jitter_strategy_decorrelated(self):
        """Factory returns DecorrelatedJitter for DECORRELATED."""
        result = get_jitter_strategy(JitterType.DECORRELATED, base_delay=2.0)
        assert isinstance(result, DecorrelatedJitter)
        assert result.base_delay == 2.0

    def test_unknown_jitter_raises(self):
        """Unknown jitter type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown jitter type"):
            get_jitter_strategy("bogus")


# ---------------------------------------------------------------------------
# RetryContext
# ---------------------------------------------------------------------------


class TestRetryContext:
    """Tests for RetryContext tracking."""

    def test_initial_state(self):
        """Fresh context has zero attempts."""
        ctx = RetryContext(operation_name="test", max_attempts=3)
        assert ctx.attempt_count == 0
        assert ctx.last_exception is None
        assert ctx.total_delay == 0.0

    def test_record_success_attempt(self):
        """Recording a successful attempt increments count."""
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(success=True, delay_before=0.5, duration=0.1)
        assert ctx.attempt_count == 1
        assert ctx.last_delay == 0.5

    def test_record_failure_attempt(self):
        """Recording a failed attempt stores exception."""
        ctx = RetryContext(operation_name="test", max_attempts=3)
        err = OSError("fail")
        ctx.record_attempt(exception=err, success=False, delay_before=1.0)
        assert ctx.last_exception is err

    def test_get_summary(self):
        """get_summary returns properly structured dict."""
        ctx = RetryContext(operation_name="my_op", max_attempts=3)
        ctx.record_attempt(success=True, delay_before=0.0, duration=0.05)
        summary = ctx.get_summary()
        assert summary["operation"] == "my_op"
        assert summary["total_attempts"] == 1
        assert summary["successful"] is True

    def test_callback_error_swallowed(self):
        """Callback errors are logged but not re-raised."""

        def bad_callback(ctx, result):
            raise RuntimeError("callback crash")

        ctx = RetryContext(
            operation_name="test",
            max_attempts=3,
            on_success=bad_callback,
        )
        # Should not raise
        ctx.trigger_success_callback("result")

    def test_repr(self):
        """repr returns readable string."""
        ctx = RetryContext(operation_name="test_op", max_attempts=5)
        assert "test_op" in repr(ctx)
        assert "0/5" in repr(ctx)


# ---------------------------------------------------------------------------
# Retry exception hierarchy
# ---------------------------------------------------------------------------


class TestRetryExceptions:
    """Tests for retry exception classes."""

    def test_max_retries_exceeded_attributes(self):
        """MaxRetriesExceeded stores attempts and operation name."""
        err = MaxRetriesExceeded(
            attempts=5,
            last_exception=OSError("inner"),
            operation="fetch_data",
        )
        assert err.attempts == 5
        assert err.operation == "fetch_data"
        assert isinstance(err.last_exception, IOError)

    def test_non_retryable_error_attributes(self):
        """NonRetryableError stores original exception."""
        original = ValueError("bad input")
        err = NonRetryableError("cannot retry", original_exception=original)
        assert err.original_exception is original

    def test_retry_timeout_attributes(self):
        """RetryTimeoutError stores timeout and attempts."""
        err = RetryTimeoutError(timeout_seconds=30.0, attempts=3)
        assert err.timeout_seconds == 30.0
        assert err.attempts == 3

    def test_invalid_config_error_attributes(self):
        """InvalidRetryConfigError stores config field."""
        err = InvalidRetryConfigError("bad value", config_field="max_attempts")
        assert err.config_field == "max_attempts"
