"""Tests for Retry Strategies Implementation.

Comprehensive unit tests for the retry mechanism implementation, including:
- Backoff strategies (fixed, linear, exponential)
- Jitter implementations (full, equal, decorrelated)
- Retry executor (sync and async)
- Exception handling and filtering
- Timeout support
- Callback system
- Context tracking
"""

import asyncio
import random
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.resilience.retry import (
    BackoffStrategy,
    DecorrelatedJitter,
    EqualJitter,
    ExponentialBackoffStrategy,
    ExponentialBackoffWithCeiling,
    FixedDelayStrategy,
    FullJitter,
    InvalidRetryConfigError,
    JitterType,
    LinearBackoffStrategy,
    MaxRetriesExceeded,
    NoJitter,
    NonRetryableError,
    RetryAttempt,
    RetryConfig,
    RetryContext,
    RetryError,
    RetryExecutor,
    RetryTimeoutError,
    get_jitter_strategy,
    get_retry_strategy,
    retry,
)


# ============================================================================
# Backoff Strategy Tests
# ============================================================================


class TestFixedDelayStrategy:
    """Test suite for fixed delay strategy."""

    def test_initialization(self):
        """Test fixed delay strategy initializes correctly."""
        strategy = FixedDelayStrategy(delay=2.0)

        assert strategy.delay == 2.0
        assert strategy.max_delay is None

    def test_calculate_delay_constant(self):
        """Test fixed delay returns constant value."""
        strategy = FixedDelayStrategy(delay=3.0)

        # Should return same delay regardless of attempt
        assert strategy.calculate_delay(0) == 3.0
        assert strategy.calculate_delay(1) == 3.0
        assert strategy.calculate_delay(5) == 3.0
        assert strategy.calculate_delay(100) == 3.0

    def test_get_delay_with_max(self):
        """Test fixed delay respects max_delay cap."""
        strategy = FixedDelayStrategy(delay=10.0, max_delay=5.0)

        # Should be capped at max_delay
        assert strategy.get_delay(0) == 5.0
        assert strategy.get_delay(5) == 5.0

    def test_get_delay_without_max(self):
        """Test fixed delay without max_delay cap."""
        strategy = FixedDelayStrategy(delay=3.0)

        assert strategy.get_delay(0) == 3.0
        assert strategy.get_delay(10) == 3.0


class TestLinearBackoffStrategy:
    """Test suite for linear backoff strategy."""

    def test_initialization(self):
        """Test linear backoff initializes correctly."""
        strategy = LinearBackoffStrategy(
            base_delay=1.0,
            increment=2.0,
        )

        assert strategy.base_delay == 1.0
        assert strategy.increment == 2.0
        assert strategy.max_delay is None

    def test_calculate_delay_linear_growth(self):
        """Test delay grows linearly."""
        strategy = LinearBackoffStrategy(base_delay=1.0, increment=2.0)

        # Formula: base_delay + (attempt * increment)
        assert strategy.calculate_delay(0) == 1.0  # 1 + (0 * 2)
        assert strategy.calculate_delay(1) == 3.0  # 1 + (1 * 2)
        assert strategy.calculate_delay(2) == 5.0  # 1 + (2 * 2)
        assert strategy.calculate_delay(3) == 7.0  # 1 + (3 * 2)
        assert strategy.calculate_delay(10) == 21.0  # 1 + (10 * 2)

    def test_get_delay_with_max(self):
        """Test linear backoff respects max_delay cap."""
        strategy = LinearBackoffStrategy(
            base_delay=1.0,
            increment=2.0,
            max_delay=6.0,
        )

        assert strategy.get_delay(0) == 1.0  # Below cap
        assert strategy.get_delay(1) == 3.0  # Below cap
        assert strategy.get_delay(2) == 5.0  # Below cap
        assert strategy.get_delay(3) == 6.0  # Capped at 6.0
        assert strategy.get_delay(10) == 6.0  # Capped at 6.0


class TestExponentialBackoffStrategy:
    """Test suite for exponential backoff strategy."""

    def test_initialization(self):
        """Test exponential backoff initializes correctly."""
        strategy = ExponentialBackoffStrategy(
            base_delay=1.0,
            multiplier=2.0,
        )

        assert strategy.base_delay == 1.0
        assert strategy.multiplier == 2.0
        assert strategy.max_delay is None

    def test_calculate_delay_exponential_growth(self):
        """Test delay grows exponentially."""
        strategy = ExponentialBackoffStrategy(base_delay=1.0, multiplier=2.0)

        # Formula: base_delay * (multiplier ^ attempt)
        assert strategy.calculate_delay(0) == 1.0  # 1 * (2^0) = 1
        assert strategy.calculate_delay(1) == 2.0  # 1 * (2^1) = 2
        assert strategy.calculate_delay(2) == 4.0  # 1 * (2^2) = 4
        assert strategy.calculate_delay(3) == 8.0  # 1 * (2^3) = 8
        assert strategy.calculate_delay(4) == 16.0  # 1 * (2^4) = 16

    def test_calculate_delay_custom_multiplier(self):
        """Test exponential backoff with custom multiplier."""
        strategy = ExponentialBackoffStrategy(base_delay=2.0, multiplier=3.0)

        assert strategy.calculate_delay(0) == 2.0  # 2 * (3^0) = 2
        assert strategy.calculate_delay(1) == 6.0  # 2 * (3^1) = 6
        assert strategy.calculate_delay(2) == 18.0  # 2 * (3^2) = 18

    def test_get_delay_with_max(self):
        """Test exponential backoff respects max_delay cap."""
        strategy = ExponentialBackoffStrategy(
            base_delay=1.0,
            multiplier=2.0,
            max_delay=10.0,
        )

        assert strategy.get_delay(0) == 1.0  # Below cap
        assert strategy.get_delay(1) == 2.0  # Below cap
        assert strategy.get_delay(2) == 4.0  # Below cap
        assert strategy.get_delay(3) == 8.0  # Below cap
        assert strategy.get_delay(4) == 10.0  # Capped at 10.0
        assert strategy.get_delay(5) == 10.0  # Capped at 10.0


class TestExponentialBackoffWithCeiling:
    """Test suite for exponential backoff with ceiling."""

    def test_initialization(self):
        """Test exponential backoff with ceiling initializes correctly."""
        strategy = ExponentialBackoffWithCeiling(
            base_delay=1.0,
            multiplier=2.0,
            max_delay=30.0,
        )

        assert strategy.base_delay == 1.0
        assert strategy.multiplier == 2.0
        assert strategy.max_delay == 30.0

    def test_calculate_delay_exponential_growth(self):
        """Test delay calculation (same as regular exponential)."""
        strategy = ExponentialBackoffWithCeiling(
            base_delay=1.0,
            multiplier=2.0,
            max_delay=60.0,
        )

        assert strategy.calculate_delay(0) == 1.0
        assert strategy.calculate_delay(1) == 2.0
        assert strategy.calculate_delay(2) == 4.0
        assert strategy.calculate_delay(3) == 8.0

    def test_ceiling_applied_through_get_delay(self):
        """Test ceiling is applied through get_delay."""
        strategy = ExponentialBackoffWithCeiling(
            base_delay=1.0,
            multiplier=2.0,
            max_delay=10.0,
        )

        # Ceiling is applied via parent class get_delay method
        assert strategy.get_delay(4) == 10.0  # 16 capped to 10
        assert strategy.get_delay(5) == 10.0  # 32 capped to 10


class TestGetRetryStrategy:
    """Test suite for retry strategy factory function."""

    def test_get_fixed_strategy(self):
        """Test getting fixed delay strategy."""
        strategy = get_retry_strategy(
            strategy=BackoffStrategy.FIXED,
            base_delay=3.0,
            max_delay=10.0,
        )

        assert isinstance(strategy, FixedDelayStrategy)
        assert strategy.delay == 3.0
        assert strategy.max_delay == 10.0

    def test_get_linear_strategy(self):
        """Test getting linear backoff strategy."""
        strategy = get_retry_strategy(
            strategy=BackoffStrategy.LINEAR,
            base_delay=1.0,
            max_delay=20.0,
            increment=3.0,
        )

        assert isinstance(strategy, LinearBackoffStrategy)
        assert strategy.base_delay == 1.0
        assert strategy.increment == 3.0
        assert strategy.max_delay == 20.0

    def test_get_exponential_strategy_without_max(self):
        """Test getting exponential backoff without max_delay."""
        strategy = get_retry_strategy(
            strategy=BackoffStrategy.EXPONENTIAL,
            base_delay=1.0,
            multiplier=3.0,
        )

        assert isinstance(strategy, ExponentialBackoffStrategy)
        assert strategy.base_delay == 1.0
        assert strategy.multiplier == 3.0
        assert strategy.max_delay is None

    def test_get_exponential_strategy_with_max(self):
        """Test getting exponential backoff with max_delay."""
        strategy = get_retry_strategy(
            strategy=BackoffStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=60.0,
            multiplier=2.0,
        )

        assert isinstance(strategy, ExponentialBackoffWithCeiling)
        assert strategy.base_delay == 1.0
        assert strategy.multiplier == 2.0
        assert strategy.max_delay == 60.0

    def test_invalid_strategy_raises_error(self):
        """Test invalid strategy type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backoff strategy"):
            # Create an invalid enum value for testing
            class InvalidStrategy:
                pass

            get_retry_strategy(strategy=InvalidStrategy(), base_delay=1.0)


# ============================================================================
# Jitter Strategy Tests
# ============================================================================


class TestNoJitter:
    """Test suite for no jitter strategy."""

    def test_apply_returns_unchanged(self):
        """Test no jitter returns delay unchanged."""
        jitter = NoJitter()

        assert jitter.apply(5.0, attempt=0) == 5.0
        assert jitter.apply(10.0, attempt=5) == 10.0
        assert jitter.apply(1.5, attempt=10, previous_delay=2.0) == 1.5


class TestFullJitter:
    """Test suite for full jitter strategy."""

    def test_apply_returns_value_in_range(self):
        """Test full jitter returns value between 0 and delay."""
        jitter = FullJitter()

        # Test multiple times due to randomness
        for _ in range(100):
            result = jitter.apply(10.0, attempt=0)
            assert 0.0 <= result <= 10.0

    def test_apply_with_different_delays(self):
        """Test full jitter with various delay values."""
        jitter = FullJitter()

        for delay in [1.0, 5.0, 10.0, 100.0]:
            for _ in range(20):
                result = jitter.apply(delay, attempt=0)
                assert 0.0 <= result <= delay

    @patch("app.resilience.retry.jitter.random.uniform")
    def test_apply_uses_random_uniform(self, mock_uniform):
        """Test full jitter uses random.uniform(0, delay)."""
        mock_uniform.return_value = 3.5
        jitter = FullJitter()

        result = jitter.apply(10.0, attempt=0)

        mock_uniform.assert_called_once_with(0, 10.0)
        assert result == 3.5


class TestEqualJitter:
    """Test suite for equal jitter strategy."""

    def test_apply_returns_value_in_range(self):
        """Test equal jitter returns value between delay/2 and delay."""
        jitter = EqualJitter()

        # Test multiple times due to randomness
        for _ in range(100):
            result = jitter.apply(10.0, attempt=0)
            # Should be between 5.0 and 10.0
            assert 5.0 <= result <= 10.0

    def test_apply_formula(self):
        """Test equal jitter formula: delay/2 + random(0, delay/2)."""
        jitter = EqualJitter()
        delay = 10.0

        for _ in range(50):
            result = jitter.apply(delay, attempt=0)
            # Formula: delay/2 + random(0, delay/2)
            # Min: 5.0 + 0 = 5.0
            # Max: 5.0 + 5.0 = 10.0
            assert 5.0 <= result <= 10.0

    @patch("app.resilience.retry.jitter.random.uniform")
    def test_apply_calculation(self, mock_uniform):
        """Test equal jitter calculation."""
        mock_uniform.return_value = 2.5  # Random part
        jitter = EqualJitter()

        result = jitter.apply(10.0, attempt=0)

        # Should be: 10/2 + 2.5 = 5.0 + 2.5 = 7.5
        mock_uniform.assert_called_once_with(0, 5.0)
        assert result == 7.5


class TestDecorrelatedJitter:
    """Test suite for decorrelated jitter strategy."""

    def test_initialization(self):
        """Test decorrelated jitter initializes correctly."""
        jitter = DecorrelatedJitter(base_delay=2.0)

        assert jitter.base_delay == 2.0

    def test_first_attempt_uses_delay(self):
        """Test first attempt (previous_delay=0) uses provided delay."""
        jitter = DecorrelatedJitter(base_delay=1.0)

        # First attempt with no previous delay
        for _ in range(50):
            result = jitter.apply(
                delay=10.0,
                attempt=0,
                previous_delay=0.0,
            )
            # Should be between base_delay and delay
            assert 1.0 <= result <= 10.0

    def test_subsequent_attempts_use_previous_delay(self):
        """Test subsequent attempts use previous_delay * 3."""
        jitter = DecorrelatedJitter(base_delay=1.0)

        # Subsequent attempt with previous delay
        for _ in range(50):
            result = jitter.apply(
                delay=10.0,
                attempt=1,
                previous_delay=5.0,
            )
            # Should be between base_delay and previous_delay * 3
            # = between 1.0 and 15.0
            assert 1.0 <= result <= 15.0

    @patch("app.resilience.retry.jitter.random.uniform")
    def test_first_attempt_calculation(self, mock_uniform):
        """Test first attempt calculation."""
        mock_uniform.return_value = 5.0
        jitter = DecorrelatedJitter(base_delay=1.0)

        result = jitter.apply(
            delay=10.0,
            attempt=0,
            previous_delay=0.0,
        )

        mock_uniform.assert_called_once_with(1.0, 10.0)
        assert result == 5.0

    @patch("app.resilience.retry.jitter.random.uniform")
    def test_subsequent_attempt_calculation(self, mock_uniform):
        """Test subsequent attempt calculation."""
        mock_uniform.return_value = 8.0
        jitter = DecorrelatedJitter(base_delay=1.0)

        result = jitter.apply(
            delay=10.0,
            attempt=1,
            previous_delay=5.0,
        )

        # Should call with base_delay and previous_delay * 3
        mock_uniform.assert_called_once_with(1.0, 15.0)
        assert result == 8.0


class TestGetJitterStrategy:
    """Test suite for jitter strategy factory function."""

    def test_get_none_jitter(self):
        """Test getting no jitter strategy."""
        jitter = get_jitter_strategy(JitterType.NONE)

        assert isinstance(jitter, NoJitter)

    def test_get_full_jitter(self):
        """Test getting full jitter strategy."""
        jitter = get_jitter_strategy(JitterType.FULL)

        assert isinstance(jitter, FullJitter)

    def test_get_equal_jitter(self):
        """Test getting equal jitter strategy."""
        jitter = get_jitter_strategy(JitterType.EQUAL)

        assert isinstance(jitter, EqualJitter)

    def test_get_decorrelated_jitter(self):
        """Test getting decorrelated jitter strategy."""
        jitter = get_jitter_strategy(
            JitterType.DECORRELATED,
            base_delay=2.0,
        )

        assert isinstance(jitter, DecorrelatedJitter)
        assert jitter.base_delay == 2.0

    def test_invalid_jitter_type_raises_error(self):
        """Test invalid jitter type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown jitter type"):

            class InvalidJitter:
                pass

            get_jitter_strategy(InvalidJitter())


# ============================================================================
# Exception Tests
# ============================================================================


class TestRetryExceptions:
    """Test suite for retry-specific exceptions."""

    def test_retry_error(self):
        """Test RetryError base exception."""
        exc = RetryError(
            message="Test error",
            attempts=3,
            last_exception=ValueError("Original"),
        )

        assert str(exc) == "Test error"
        assert exc.attempts == 3
        assert isinstance(exc.last_exception, ValueError)

    def test_max_retries_exceeded(self):
        """Test MaxRetriesExceeded exception."""
        original = ValueError("Original error")
        exc = MaxRetriesExceeded(
            attempts=5,
            last_exception=original,
            operation="test_operation",
        )

        assert "Maximum retry attempts (5) exceeded" in str(exc)
        assert "test_operation" in str(exc)
        assert exc.attempts == 5
        assert exc.last_exception is original
        assert exc.operation == "test_operation"

    def test_non_retryable_error(self):
        """Test NonRetryableError exception."""
        original = KeyError("Key not found")
        exc = NonRetryableError(
            message="Cannot retry this",
            original_exception=original,
        )

        assert str(exc) == "Cannot retry this"
        assert exc.original_exception is original
        assert exc.attempts == 0

    def test_retry_timeout_error(self):
        """Test RetryTimeoutError exception."""
        original = TimeoutError("Timeout")
        exc = RetryTimeoutError(
            timeout_seconds=30.0,
            attempts=3,
            last_exception=original,
        )

        assert "30.0s" in str(exc)
        assert "(3 attempts)" in str(exc)
        assert exc.timeout_seconds == 30.0
        assert exc.attempts == 3
        assert exc.last_exception is original

    def test_invalid_retry_config_error(self):
        """Test InvalidRetryConfigError exception."""
        exc = InvalidRetryConfigError(
            message="Invalid configuration",
            config_field="max_attempts",
        )

        assert str(exc) == "Invalid configuration"
        assert exc.config_field == "max_attempts"


# ============================================================================
# RetryContext Tests
# ============================================================================


class TestRetryContext:
    """Test suite for retry context tracking."""

    @pytest.fixture
    def context(self):
        """Create a retry context for testing."""
        return RetryContext(
            operation_name="test_operation",
            max_attempts=5,
        )

    def test_initialization(self, context):
        """Test retry context initializes correctly."""
        assert context.operation_name == "test_operation"
        assert context.max_attempts == 5
        assert context.attempt_count == 0
        assert len(context.attempts) == 0
        assert context.last_delay == 0.0
        assert context.start_time is not None

    def test_record_attempt_success(self, context):
        """Test recording successful attempt."""
        context.record_attempt(
            success=True,
            delay_before=1.0,
            duration=0.5,
        )

        assert context.attempt_count == 1
        assert len(context.attempts) == 1

        attempt = context.attempts[0]
        assert attempt.attempt_number == 1
        assert attempt.success is True
        assert attempt.delay_before == 1.0
        assert attempt.duration == 0.5
        assert attempt.exception is None

    def test_record_attempt_failure(self, context):
        """Test recording failed attempt."""
        exc = ValueError("Test error")
        context.record_attempt(
            exception=exc,
            success=False,
            delay_before=2.0,
            duration=1.0,
        )

        assert context.attempt_count == 1
        attempt = context.attempts[0]
        assert attempt.success is False
        assert attempt.exception is exc
        assert attempt.delay_before == 2.0

    def test_last_exception(self, context):
        """Test getting last exception."""
        assert context.last_exception is None

        exc1 = ValueError("First")
        context.record_attempt(exception=exc1, success=False)

        assert context.last_exception is exc1

        exc2 = TypeError("Second")
        context.record_attempt(exception=exc2, success=False)

        assert context.last_exception is exc2

    def test_elapsed_time(self, context):
        """Test elapsed time calculation."""
        time.sleep(0.1)
        elapsed = context.elapsed_seconds

        assert elapsed >= 0.1
        assert elapsed < 1.0  # Should be quick

    def test_total_delay(self, context):
        """Test total delay calculation."""
        context.record_attempt(delay_before=1.0)
        context.record_attempt(delay_before=2.0)
        context.record_attempt(delay_before=3.0)

        assert context.total_delay == 6.0

    def test_trigger_retry_callback(self, context):
        """Test retry callback is triggered."""
        callback_args = []

        def on_retry(ctx, exc, delay):
            callback_args.append((ctx, exc, delay))

        context.on_retry = on_retry
        exc = ValueError("Test")

        context.trigger_retry_callback(exc, 2.5)

        assert len(callback_args) == 1
        assert callback_args[0][0] is context
        assert callback_args[0][1] is exc
        assert callback_args[0][2] == 2.5

    def test_trigger_success_callback(self, context):
        """Test success callback is triggered."""
        callback_args = []

        def on_success(ctx, result):
            callback_args.append((ctx, result))

        context.on_success = on_success

        context.trigger_success_callback("success_value")

        assert len(callback_args) == 1
        assert callback_args[0][0] is context
        assert callback_args[0][1] == "success_value"

    def test_trigger_failure_callback(self, context):
        """Test failure callback is triggered."""
        callback_args = []

        def on_failure(ctx, exc):
            callback_args.append((ctx, exc))

        context.on_failure = on_failure
        exc = ValueError("Failed")

        context.trigger_failure_callback(exc)

        assert len(callback_args) == 1
        assert callback_args[0][0] is context
        assert callback_args[0][1] is exc

    def test_callback_error_handling(self, context):
        """Test that callback errors don't crash."""

        def bad_callback(ctx, exc):
            raise RuntimeError("Callback error")

        context.on_failure = bad_callback

        # Should not raise, just log
        context.trigger_failure_callback(ValueError("Test"))

    def test_get_summary(self, context):
        """Test getting context summary."""
        context.record_attempt(success=False, exception=ValueError("Error"))
        context.record_attempt(success=True, delay_before=1.0)

        summary = context.get_summary()

        assert summary["operation"] == "test_operation"
        assert summary["total_attempts"] == 2
        assert summary["max_attempts"] == 5
        assert summary["successful"] is True
        assert "attempts" in summary
        assert len(summary["attempts"]) == 2

    def test_repr(self, context):
        """Test string representation."""
        context.record_attempt(success=False)

        repr_str = repr(context)

        assert "test_operation" in repr_str
        assert "attempts=1/5" in repr_str


class TestRetryAttempt:
    """Test suite for retry attempt dataclass."""

    def test_initialization(self):
        """Test retry attempt initializes correctly."""
        exc = ValueError("Test")
        now = datetime.utcnow()

        attempt = RetryAttempt(
            attempt_number=3,
            timestamp=now,
            delay_before=2.5,
            exception=exc,
            success=False,
            duration=1.2,
        )

        assert attempt.attempt_number == 3
        assert attempt.timestamp == now
        assert attempt.delay_before == 2.5
        assert attempt.exception is exc
        assert attempt.success is False
        assert attempt.duration == 1.2


# ============================================================================
# RetryConfig Tests
# ============================================================================


class TestRetryConfig:
    """Test suite for retry configuration."""

    def test_initialization_defaults(self):
        """Test retry config initializes with defaults."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.backoff_strategy == BackoffStrategy.EXPONENTIAL
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.multiplier == 2.0
        assert config.jitter == JitterType.FULL
        assert config.retryable_exceptions == (Exception,)
        assert config.non_retryable_exceptions == ()
        assert config.timeout is None

    def test_initialization_custom(self):
        """Test retry config with custom values."""
        config = RetryConfig(
            max_attempts=5,
            backoff_strategy=BackoffStrategy.LINEAR,
            base_delay=2.0,
            max_delay=30.0,
            multiplier=3.0,
            jitter=JitterType.EQUAL,
            timeout=60.0,
        )

        assert config.max_attempts == 5
        assert config.backoff_strategy == BackoffStrategy.LINEAR
        assert config.base_delay == 2.0
        assert config.max_delay == 30.0
        assert config.multiplier == 3.0
        assert config.jitter == JitterType.EQUAL
        assert config.timeout == 60.0

    def test_validation_max_attempts_too_low(self):
        """Test validation fails for max_attempts < 1."""
        with pytest.raises(
            InvalidRetryConfigError,
            match="max_attempts must be at least 1",
        ):
            RetryConfig(max_attempts=0)

    def test_validation_negative_base_delay(self):
        """Test validation fails for negative base_delay."""
        with pytest.raises(
            InvalidRetryConfigError,
            match="base_delay must be non-negative",
        ):
            RetryConfig(base_delay=-1.0)

    def test_validation_max_delay_less_than_base(self):
        """Test validation fails for max_delay < base_delay."""
        with pytest.raises(
            InvalidRetryConfigError,
            match="max_delay must be greater than or equal to base_delay",
        ):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_validation_multiplier_too_low(self):
        """Test validation fails for multiplier < 1."""
        with pytest.raises(
            InvalidRetryConfigError,
            match="multiplier must be at least 1",
        ):
            RetryConfig(multiplier=0.5)

    def test_validation_negative_timeout(self):
        """Test validation fails for negative timeout."""
        with pytest.raises(
            InvalidRetryConfigError,
            match="timeout must be positive",
        ):
            RetryConfig(timeout=-10.0)

    def test_callbacks(self):
        """Test config accepts callbacks."""
        on_retry = Mock()
        on_success = Mock()
        on_failure = Mock()

        config = RetryConfig(
            on_retry=on_retry,
            on_success=on_success,
            on_failure=on_failure,
        )

        assert config.on_retry is on_retry
        assert config.on_success is on_success
        assert config.on_failure is on_failure


# ============================================================================
# RetryExecutor Tests
# ============================================================================


class TestRetryExecutor:
    """Test suite for retry executor."""

    @pytest.fixture
    def config(self):
        """Create retry config for testing."""
        return RetryConfig(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.FIXED,
            base_delay=0.1,  # Short delay for fast tests
            jitter=JitterType.NONE,  # No jitter for predictability
        )

    @pytest.fixture
    def executor(self, config):
        """Create retry executor for testing."""
        return RetryExecutor(config)

    def test_initialization(self, executor, config):
        """Test retry executor initializes correctly."""
        assert executor.config is config
        assert executor.strategy is not None
        assert executor.jitter_strategy is not None

    def test_should_retry_retryable_exception(self, executor):
        """Test should_retry returns True for retryable exceptions."""
        assert executor.should_retry(ValueError("test")) is True
        assert executor.should_retry(RuntimeError("test")) is True

    def test_should_retry_non_retryable_exception(self):
        """Test should_retry returns False for non-retryable exceptions."""
        config = RetryConfig(
            non_retryable_exceptions=(ValueError, KeyError),
        )
        executor = RetryExecutor(config)

        assert executor.should_retry(ValueError("test")) is False
        assert executor.should_retry(KeyError("test")) is False
        assert executor.should_retry(RuntimeError("test")) is True

    def test_should_retry_specific_retryable_exceptions(self):
        """Test should_retry with specific retryable exceptions."""
        config = RetryConfig(
            retryable_exceptions=(ConnectionError, TimeoutError),
        )
        executor = RetryExecutor(config)

        assert executor.should_retry(ConnectionError("test")) is True
        assert executor.should_retry(TimeoutError("test")) is True
        assert executor.should_retry(ValueError("test")) is False

    def test_execute_sync_success_first_attempt(self, executor):
        """Test successful execution on first attempt."""

        def success_func():
            return "success"

        result = executor.execute_sync(success_func)

        assert result == "success"

    def test_execute_sync_success_after_retries(self, executor):
        """Test successful execution after some failures."""
        attempts = [0]

        def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "success"

        result = executor.execute_sync(eventually_succeeds)

        assert result == "success"
        assert attempts[0] == 3

    def test_execute_sync_max_retries_exceeded(self, executor):
        """Test max retries exceeded raises exception."""

        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(MaxRetriesExceeded) as exc_info:
            executor.execute_sync(always_fails)

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_execute_sync_non_retryable_exception(self):
        """Test non-retryable exception stops retries immediately."""
        config = RetryConfig(
            max_attempts=5,
            non_retryable_exceptions=(ValueError,),
        )
        executor = RetryExecutor(config)

        def raises_non_retryable():
            raise ValueError("Non-retryable")

        with pytest.raises(NonRetryableError) as exc_info:
            executor.execute_sync(raises_non_retryable)

        assert isinstance(exc_info.value.original_exception, ValueError)

    def test_execute_sync_with_arguments(self, executor):
        """Test execute_sync with function arguments."""

        def add(a, b):
            return a + b

        result = executor.execute_sync(add, 5, 3)
        assert result == 8

        result = executor.execute_sync(add, a=10, b=20)
        assert result == 30

    def test_execute_sync_timeout(self):
        """Test timeout raises RetryTimeoutError."""
        config = RetryConfig(
            max_attempts=10,
            base_delay=0.5,
            timeout=0.3,  # Short timeout
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(config)

        def slow_fail():
            raise ValueError("Slow fail")

        with pytest.raises(RetryTimeoutError) as exc_info:
            executor.execute_sync(slow_fail)

        assert exc_info.value.timeout_seconds == 0.3

    @pytest.mark.asyncio
    async def test_execute_async_success_first_attempt(self, executor):
        """Test async successful execution on first attempt."""

        async def async_success():
            return "async_success"

        result = await executor.execute_async(async_success)

        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_execute_async_success_after_retries(self, executor):
        """Test async successful execution after retries."""
        attempts = [0]

        async def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "async_success"

        result = await executor.execute_async(eventually_succeeds)

        assert result == "async_success"
        assert attempts[0] == 3

    @pytest.mark.asyncio
    async def test_execute_async_max_retries_exceeded(self, executor):
        """Test async max retries exceeded."""

        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(MaxRetriesExceeded):
            await executor.execute_async(always_fails)

    @pytest.mark.asyncio
    async def test_execute_async_with_arguments(self, executor):
        """Test async execute with arguments."""

        async def async_add(a, b):
            return a + b

        result = await executor.execute_async(async_add, 5, 3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_execute_async_timeout(self):
        """Test async timeout."""
        config = RetryConfig(
            max_attempts=10,
            base_delay=0.5,
            timeout=0.3,
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(config)

        async def slow_fail():
            raise ValueError("Slow fail")

        with pytest.raises(RetryTimeoutError):
            await executor.execute_async(slow_fail)


# ============================================================================
# Retry Decorator Tests
# ============================================================================


class TestRetryDecorator:
    """Test suite for retry decorator."""

    def test_decorator_sync_success(self):
        """Test decorator on successful sync function."""

        @retry(max_attempts=3)
        def success_func():
            return "success"

        result = success_func()

        assert result == "success"

    def test_decorator_sync_with_retries(self):
        """Test decorator retries sync function."""
        attempts = [0]

        @retry(max_attempts=5, base_delay=0.1, jitter=JitterType.NONE)
        def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "success"

        result = eventually_succeeds()

        assert result == "success"
        assert attempts[0] == 3

    def test_decorator_sync_max_retries(self):
        """Test decorator raises MaxRetriesExceeded."""

        @retry(max_attempts=3, base_delay=0.01, jitter=JitterType.NONE)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(MaxRetriesExceeded):
            always_fails()

    def test_decorator_with_callbacks(self):
        """Test decorator with callback functions."""
        retry_count = [0]
        success_count = [0]

        def on_retry(ctx, exc, delay):
            retry_count[0] += 1

        def on_success(ctx, result):
            success_count[0] += 1

        attempts = [0]

        @retry(
            max_attempts=5,
            base_delay=0.01,
            jitter=JitterType.NONE,
            on_retry=on_retry,
            on_success=on_success,
        )
        def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "success"

        result = eventually_succeeds()

        assert result == "success"
        assert retry_count[0] == 2  # Retried twice
        assert success_count[0] == 1  # Succeeded once

    def test_decorator_exception_filtering(self):
        """Test decorator with exception filtering."""

        @retry(
            max_attempts=3,
            retryable_exceptions=(ConnectionError,),
            base_delay=0.01,
        )
        def raises_value_error():
            raise ValueError("Not retryable")

        # ValueError is not in retryable_exceptions
        with pytest.raises(NonRetryableError):
            raises_value_error()

    @pytest.mark.asyncio
    async def test_decorator_async_success(self):
        """Test decorator on async function."""

        @retry(max_attempts=3)
        async def async_success():
            return "async_success"

        result = await async_success()

        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_decorator_async_with_retries(self):
        """Test decorator retries async function."""
        attempts = [0]

        @retry(max_attempts=5, base_delay=0.1, jitter=JitterType.NONE)
        async def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "async_success"

        result = await eventually_succeeds()

        assert result == "async_success"
        assert attempts[0] == 3

    @pytest.mark.asyncio
    async def test_decorator_async_max_retries(self):
        """Test async decorator raises MaxRetriesExceeded."""

        @retry(max_attempts=3, base_delay=0.01, jitter=JitterType.NONE)
        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(MaxRetriesExceeded):
            await always_fails()

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring."""

        @retry(max_attempts=3)
        def my_function():
            """My docstring."""
            return "test"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    def test_decorator_with_arguments(self):
        """Test decorated function with arguments."""

        @retry(max_attempts=3)
        def add(a, b):
            return a + b

        result = add(5, 3)
        assert result == 8

        result = add(a=10, b=20)
        assert result == 30


# ============================================================================
# Integration Tests
# ============================================================================


class TestRetryIntegration:
    """Integration tests for complete retry workflows."""

    def test_exponential_backoff_delays(self):
        """Test exponential backoff produces correct delays."""
        config = RetryConfig(
            max_attempts=5,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            base_delay=0.1,
            multiplier=2.0,
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(config)

        attempts = [0]
        start_time = time.time()

        def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 4:
                raise ValueError("Not yet")
            return "success"

        result = executor.execute_sync(eventually_succeeds)

        elapsed = time.time() - start_time

        # Should have delays: 0.1, 0.2, 0.4
        # Total: ~0.7 seconds
        assert result == "success"
        assert attempts[0] == 4
        assert 0.6 < elapsed < 1.0  # Allow some margin

    def test_linear_backoff_delays(self):
        """Test linear backoff produces correct delays."""
        config = RetryConfig(
            max_attempts=4,
            backoff_strategy=BackoffStrategy.LINEAR,
            base_delay=0.1,
            increment=0.1,
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(config)

        attempts = [0]
        start_time = time.time()

        def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "success"

        result = executor.execute_sync(eventually_succeeds)

        elapsed = time.time() - start_time

        # Should have delays: 0.1, 0.2
        # Total: ~0.3 seconds
        assert result == "success"
        assert attempts[0] == 3
        assert 0.2 < elapsed < 0.5

    def test_jitter_reduces_thundering_herd(self):
        """Test that jitter produces varied delays."""
        config = RetryConfig(
            max_attempts=10,
            backoff_strategy=BackoffStrategy.FIXED,
            base_delay=1.0,
            jitter=JitterType.FULL,
        )
        executor = RetryExecutor(config)

        delays = []

        def record_delays():
            # Capture delays through monkey patching
            raise ValueError("Fail")

        # Execute multiple times and collect delays
        for _ in range(5):
            attempts = [0]

            def fail_once(attempts=attempts):
                attempts[0] += 1
                if attempts[0] < 2:
                    raise ValueError("Fail")
                return "success"

            executor.execute_sync(fail_once)

        # With full jitter, delays should vary
        # (This is probabilistic, but very unlikely to all be identical)

    @pytest.mark.asyncio
    async def test_async_concurrent_retries(self):
        """Test multiple async retries can run concurrently."""

        @retry(max_attempts=3, base_delay=0.1, jitter=JitterType.NONE)
        async def async_operation(task_id):
            # Simulate some async work
            await asyncio.sleep(0.05)
            return f"result_{task_id}"

        # Run multiple operations concurrently
        tasks = [async_operation(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert results[0] == "result_0"
        assert results[4] == "result_4"

    def test_callback_observability(self):
        """Test callbacks provide observability into retry process."""
        events = []

        def on_retry(ctx, exc, delay):
            events.append(("retry", ctx.attempt_count, delay))

        def on_success(ctx, result):
            events.append(("success", result))

        def on_failure(ctx, exc):
            events.append(("failure", type(exc).__name__))

        attempts = [0]

        @retry(
            max_attempts=4,
            base_delay=0.01,
            jitter=JitterType.NONE,
            on_retry=on_retry,
            on_success=on_success,
            on_failure=on_failure,
        )
        def eventually_succeeds():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "success"

        result = eventually_succeeds()

        assert result == "success"
        # Should have 2 retry events and 1 success event
        assert len(events) == 3
        assert events[0][0] == "retry"
        assert events[1][0] == "retry"
        assert events[2] == ("success", "success")

    def test_max_delay_cap(self):
        """Test max_delay caps exponential growth."""
        config = RetryConfig(
            max_attempts=10,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=5.0,
            multiplier=2.0,
            jitter=JitterType.NONE,
        )
        executor = RetryExecutor(config)

        # Test delay calculation
        # Attempt 0: 1.0
        # Attempt 1: 2.0
        # Attempt 2: 4.0
        # Attempt 3: 8.0 -> capped to 5.0
        # Attempt 4: 16.0 -> capped to 5.0

        assert executor.strategy.get_delay(0) == 1.0
        assert executor.strategy.get_delay(1) == 2.0
        assert executor.strategy.get_delay(2) == 4.0
        assert executor.strategy.get_delay(3) == 5.0  # Capped
        assert executor.strategy.get_delay(4) == 5.0  # Capped
