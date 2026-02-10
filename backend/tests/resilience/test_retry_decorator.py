"""Tests for retry decorator (pure logic, no DB)."""

import pytest

from app.resilience.retry.decorator import (
    RetryConfig,
    RetryExecutor,
)
from app.resilience.retry.exceptions import (
    InvalidRetryConfigError,
    MaxRetriesExceeded,
    NonRetryableError,
)
from app.resilience.retry.jitter import JitterType
from app.resilience.retry.strategies import BackoffStrategy


# -- RetryConfig defaults ----------------------------------------------------


class TestRetryConfigDefaults:
    def test_default_values(self):
        cfg = RetryConfig()
        assert cfg.max_attempts == 3
        assert cfg.backoff_strategy == BackoffStrategy.EXPONENTIAL
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 60.0
        assert cfg.multiplier == 2.0
        assert cfg.jitter == JitterType.FULL
        assert cfg.retryable_exceptions == (Exception,)
        assert cfg.non_retryable_exceptions == ()
        assert cfg.timeout is None
        assert cfg.on_retry is None
        assert cfg.on_success is None
        assert cfg.on_failure is None


# -- RetryConfig validation --------------------------------------------------


class TestRetryConfigValidation:
    def test_valid_config(self):
        cfg = RetryConfig(
            max_attempts=5, base_delay=0.5, max_delay=10.0, multiplier=3.0
        )
        assert cfg.max_attempts == 5

    def test_max_attempts_zero_raises(self):
        with pytest.raises(InvalidRetryConfigError, match="max_attempts"):
            RetryConfig(max_attempts=0)

    def test_max_attempts_negative_raises(self):
        with pytest.raises(InvalidRetryConfigError, match="max_attempts"):
            RetryConfig(max_attempts=-1)

    def test_base_delay_negative_raises(self):
        with pytest.raises(InvalidRetryConfigError, match="base_delay"):
            RetryConfig(base_delay=-0.5)

    def test_base_delay_zero_ok(self):
        cfg = RetryConfig(base_delay=0.0, max_delay=None)
        assert cfg.base_delay == 0.0

    def test_max_delay_less_than_base_raises(self):
        with pytest.raises(InvalidRetryConfigError, match="max_delay"):
            RetryConfig(base_delay=5.0, max_delay=1.0)

    def test_max_delay_none_ok(self):
        cfg = RetryConfig(max_delay=None)
        assert cfg.max_delay is None

    def test_max_delay_equal_to_base_ok(self):
        cfg = RetryConfig(base_delay=1.0, max_delay=1.0)
        assert cfg.max_delay == 1.0

    def test_multiplier_below_one_raises(self):
        with pytest.raises(InvalidRetryConfigError, match="multiplier"):
            RetryConfig(multiplier=0.5)

    def test_multiplier_one_ok(self):
        cfg = RetryConfig(multiplier=1.0)
        assert cfg.multiplier == 1.0

    def test_timeout_zero_raises(self):
        with pytest.raises(InvalidRetryConfigError, match="timeout"):
            RetryConfig(timeout=0.0)

    def test_timeout_negative_raises(self):
        with pytest.raises(InvalidRetryConfigError, match="timeout"):
            RetryConfig(timeout=-1.0)

    def test_timeout_positive_ok(self):
        cfg = RetryConfig(timeout=30.0)
        assert cfg.timeout == 30.0

    def test_config_field_set_on_error(self):
        with pytest.raises(InvalidRetryConfigError) as exc_info:
            RetryConfig(max_attempts=0)
        assert exc_info.value.config_field == "max_attempts"


# -- RetryExecutor should_retry -----------------------------------------------


class TestRetryExecutorShouldRetry:
    def test_retryable_exception_returns_true(self):
        cfg = RetryConfig(retryable_exceptions=(ValueError,))
        executor = RetryExecutor(cfg)
        assert executor.should_retry(ValueError("test")) is True

    def test_non_matching_exception_returns_false(self):
        cfg = RetryConfig(retryable_exceptions=(ValueError,))
        executor = RetryExecutor(cfg)
        assert executor.should_retry(TypeError("test")) is False

    def test_non_retryable_overrides_retryable(self):
        cfg = RetryConfig(
            retryable_exceptions=(Exception,),
            non_retryable_exceptions=(ValueError,),
        )
        executor = RetryExecutor(cfg)
        assert executor.should_retry(ValueError("test")) is False
        assert executor.should_retry(TypeError("test")) is True

    def test_default_retries_all_exceptions(self):
        cfg = RetryConfig()
        executor = RetryExecutor(cfg)
        assert executor.should_retry(RuntimeError("test")) is True
        assert executor.should_retry(ValueError("test")) is True

    def test_subclass_exceptions(self):
        cfg = RetryConfig(retryable_exceptions=(OSError,))
        executor = RetryExecutor(cfg)
        assert (
            executor.should_retry(FileNotFoundError("test")) is True
        )  # subclass of OSError
        assert executor.should_retry(ValueError("test")) is False


# -- RetryExecutor execute_sync -----------------------------------------------


class TestRetryExecutorExecuteSync:
    def test_success_on_first_try(self):
        cfg = RetryConfig(
            max_attempts=3, base_delay=0.0, max_delay=None, jitter=JitterType.NONE
        )
        executor = RetryExecutor(cfg)

        def success_func():
            return 42

        result = executor.execute_sync(success_func)
        assert result == 42

    def test_retries_on_failure(self):
        cfg = RetryConfig(
            max_attempts=3,
            base_delay=0.0,
            max_delay=None,
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(cfg)

        call_count = 0

        def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = executor.execute_sync(failing_then_succeeding)
        assert result == "ok"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        cfg = RetryConfig(
            max_attempts=2,
            base_delay=0.0,
            max_delay=None,
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(cfg)

        def always_fails():
            raise ValueError("boom")

        with pytest.raises(MaxRetriesExceeded) as exc_info:
            executor.execute_sync(always_fails)
        assert exc_info.value.attempts == 2

    def test_non_retryable_exception_stops_immediately(self):
        cfg = RetryConfig(
            max_attempts=5,
            base_delay=0.0,
            max_delay=None,
            jitter=JitterType.NONE,
            non_retryable_exceptions=(ValueError,),
        )
        executor = RetryExecutor(cfg)

        call_count = 0

        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("non-retryable")

        with pytest.raises(NonRetryableError):
            executor.execute_sync(raises_value_error)
        assert call_count == 1  # Only called once

    def test_callbacks_called(self):
        success_called = []
        failure_called = []
        retry_called = []

        cfg = RetryConfig(
            max_attempts=3,
            base_delay=0.0,
            max_delay=None,
            jitter=JitterType.NONE,
            on_success=lambda ctx, result: success_called.append(result),
            on_failure=lambda ctx, exc: failure_called.append(exc),
            on_retry=lambda ctx, exc, delay: retry_called.append(exc),
        )
        executor = RetryExecutor(cfg)

        call_count = 0

        def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("first attempt")
            return "success"

        result = executor.execute_sync(fails_once)
        assert result == "success"
        assert len(success_called) == 1
        assert len(retry_called) == 1
        assert len(failure_called) == 0

    def test_single_attempt_config(self):
        cfg = RetryConfig(
            max_attempts=1,
            base_delay=0.0,
            max_delay=None,
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(cfg)

        def always_fails():
            raise ValueError("boom")

        with pytest.raises(MaxRetriesExceeded):
            executor.execute_sync(always_fails)
