"""
Retry decorator for automatic retry with backoff.

Provides a decorator and function wrapper for automatic retry with:
- Configurable backoff strategies
- Jitter support
- Exception filtering
- Callbacks for observability
- Metrics integration
- Async support
"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from app.resilience.retry.context import RetryContext
from app.resilience.retry.exceptions import (
    InvalidRetryConfigError,
    MaxRetriesExceeded,
    NonRetryableError,
    RetryTimeoutError,
)
from app.resilience.retry.jitter import JitterType, get_jitter_strategy
from app.resilience.retry.strategies import BackoffStrategy, get_retry_strategy

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float | None = 60.0,
        multiplier: float = 2.0,
        jitter: JitterType = JitterType.FULL,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
        non_retryable_exceptions: tuple[type[Exception], ...] = (),
        timeout: float | None = None,
        on_retry: Callable[[RetryContext, Exception, float], None] | None = None,
        on_success: Callable[[RetryContext, Any], None] | None = None,
        on_failure: Callable[[RetryContext, Exception], None] | None = None,
    ) -> None:
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of attempts (including initial call)
            backoff_strategy: Strategy for calculating delays
            base_delay: Base delay for backoff strategy (seconds)
            max_delay: Maximum delay cap (seconds)
            multiplier: Multiplier for exponential backoff
            jitter: Jitter type to apply to delays
            retryable_exceptions: Tuple of exception types that should trigger retry
            non_retryable_exceptions: Tuple of exception types that should NOT retry
            timeout: Maximum total time for all retries (seconds)
            on_retry: Callback called before each retry
            on_success: Callback called on successful completion
            on_failure: Callback called when all retries exhausted

        Raises:
            InvalidRetryConfigError: If configuration is invalid
        """
        # Validation
        if max_attempts < 1:
            raise InvalidRetryConfigError(
                "max_attempts must be at least 1",
                config_field="max_attempts",
            )
        if base_delay < 0:
            raise InvalidRetryConfigError(
                "base_delay must be non-negative",
                config_field="base_delay",
            )
        if max_delay is not None and max_delay < base_delay:
            raise InvalidRetryConfigError(
                "max_delay must be greater than or equal to base_delay",
                config_field="max_delay",
            )
        if multiplier < 1:
            raise InvalidRetryConfigError(
                "multiplier must be at least 1",
                config_field="multiplier",
            )
        if timeout is not None and timeout <= 0:
            raise InvalidRetryConfigError(
                "timeout must be positive",
                config_field="timeout",
            )

        self.max_attempts = max_attempts
        self.backoff_strategy = backoff_strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.non_retryable_exceptions = non_retryable_exceptions
        self.timeout = timeout
        self.on_retry = on_retry
        self.on_success = on_success
        self.on_failure = on_failure


class RetryExecutor:
    """Executes retry logic for a callable."""

    def __init__(self, config: RetryConfig) -> None:
        """
        Initialize retry executor.

        Args:
            config: Retry configuration
        """
        self.config = config
        self.strategy = get_retry_strategy(
            strategy=config.backoff_strategy,
            base_delay=config.base_delay,
            max_delay=config.max_delay,
            multiplier=config.multiplier,
        )
        self.jitter_strategy = get_jitter_strategy(
            jitter_type=config.jitter,
            base_delay=config.base_delay,
        )

    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if an exception should trigger a retry.

        Args:
            exception: The exception to check

        Returns:
            True if should retry, False otherwise
        """
        # Non-retryable exceptions always prevent retry
        if isinstance(exception, self.config.non_retryable_exceptions):
            return False

            # Check if it matches retryable exceptions
        return isinstance(exception, self.config.retryable_exceptions)

    def execute_sync(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute a synchronous function with retry.

        Args:
            func: The function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            The result of the function call

        Raises:
            MaxRetriesExceeded: If all retry attempts are exhausted
            NonRetryableError: If a non-retryable exception occurs
            RetryTimeoutError: If timeout is exceeded
        """
        operation_name = getattr(func, "__name__", "unknown")
        context = RetryContext(
            operation_name=operation_name,
            max_attempts=self.config.max_attempts,
            on_retry=self.config.on_retry,
            on_success=self.config.on_success,
            on_failure=self.config.on_failure,
        )

        attempt = 0
        last_exception = None

        while attempt < self.config.max_attempts:
            # Check timeout
            if self.config.timeout and context.elapsed_seconds > self.config.timeout:
                error = RetryTimeoutError(
                    timeout_seconds=self.config.timeout,
                    attempts=attempt,
                    last_exception=last_exception,
                )
                context.trigger_failure_callback(error)
                raise error

                # Calculate delay for this attempt
            if attempt > 0:
                base_delay = self.strategy.get_delay(attempt - 1)
                delay = self.jitter_strategy.apply(
                    delay=base_delay,
                    attempt=attempt - 1,
                    previous_delay=context.last_delay,
                )

                # Sleep before retry
                logger.debug(
                    f"Retrying {operation_name} (attempt {attempt + 1}/{self.config.max_attempts}) "
                    f"after {delay:.2f}s delay"
                )
                time.sleep(delay)
            else:
                delay = 0.0

                # Execute the function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Success!
                context.record_attempt(
                    success=True, delay_before=delay, duration=duration
                )
                context.trigger_success_callback(result)
                return result

            except Exception as e:
                duration = time.time() - start_time
                last_exception = e

                # Record the failed attempt
                context.record_attempt(
                    exception=e,
                    success=False,
                    delay_before=delay,
                    duration=duration,
                )

                # Check if we should retry
                if not self.should_retry(e):
                    error = NonRetryableError(
                        f"Non-retryable exception in {operation_name}: {type(e).__name__}",
                        original_exception=e,
                    )
                    context.trigger_failure_callback(error)
                    raise error

                attempt += 1

                # If we have attempts left, trigger retry callback
                if attempt < self.config.max_attempts:
                    next_delay = self.jitter_strategy.apply(
                        delay=self.strategy.get_delay(attempt - 1),
                        attempt=attempt - 1,
                        previous_delay=context.last_delay,
                    )
                    context.trigger_retry_callback(e, next_delay)

                    # All retries exhausted
        error = MaxRetriesExceeded(
            attempts=attempt,
            last_exception=last_exception,
            operation=operation_name,
        )
        context.trigger_failure_callback(error)
        raise error

    async def execute_async(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute an async function with retry.

        Args:
            func: The async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            The result of the function call

        Raises:
            MaxRetriesExceeded: If all retry attempts are exhausted
            NonRetryableError: If a non-retryable exception occurs
            RetryTimeoutError: If timeout is exceeded
        """
        operation_name = getattr(func, "__name__", "unknown")
        context = RetryContext(
            operation_name=operation_name,
            max_attempts=self.config.max_attempts,
            on_retry=self.config.on_retry,
            on_success=self.config.on_success,
            on_failure=self.config.on_failure,
        )

        attempt = 0
        last_exception = None

        while attempt < self.config.max_attempts:
            # Check timeout
            if self.config.timeout and context.elapsed_seconds > self.config.timeout:
                error = RetryTimeoutError(
                    timeout_seconds=self.config.timeout,
                    attempts=attempt,
                    last_exception=last_exception,
                )
                context.trigger_failure_callback(error)
                raise error

                # Calculate delay for this attempt
            if attempt > 0:
                base_delay = self.strategy.get_delay(attempt - 1)
                delay = self.jitter_strategy.apply(
                    delay=base_delay,
                    attempt=attempt - 1,
                    previous_delay=context.last_delay,
                )

                # Async sleep before retry
                logger.debug(
                    f"Retrying {operation_name} (attempt {attempt + 1}/{self.config.max_attempts}) "
                    f"after {delay:.2f}s delay"
                )
                await asyncio.sleep(delay)
            else:
                delay = 0.0

                # Execute the function
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Success!
                context.record_attempt(
                    success=True, delay_before=delay, duration=duration
                )
                context.trigger_success_callback(result)
                return result

            except Exception as e:
                duration = time.time() - start_time
                last_exception = e

                # Record the failed attempt
                context.record_attempt(
                    exception=e,
                    success=False,
                    delay_before=delay,
                    duration=duration,
                )

                # Check if we should retry
                if not self.should_retry(e):
                    error = NonRetryableError(
                        f"Non-retryable exception in {operation_name}: {type(e).__name__}",
                        original_exception=e,
                    )
                    context.trigger_failure_callback(error)
                    raise error

                attempt += 1

                # If we have attempts left, trigger retry callback
                if attempt < self.config.max_attempts:
                    next_delay = self.jitter_strategy.apply(
                        delay=self.strategy.get_delay(attempt - 1),
                        attempt=attempt - 1,
                        previous_delay=context.last_delay,
                    )
                    context.trigger_retry_callback(e, next_delay)

                    # All retries exhausted
        error = MaxRetriesExceeded(
            attempts=attempt,
            last_exception=last_exception,
            operation=operation_name,
        )
        context.trigger_failure_callback(error)
        raise error


def retry(
    max_attempts: int = 3,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    max_delay: float | None = 60.0,
    multiplier: float = 2.0,
    jitter: JitterType = JitterType.FULL,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    non_retryable_exceptions: tuple[type[Exception], ...] = (),
    timeout: float | None = None,
    on_retry: Callable[[RetryContext, Exception, float], None] | None = None,
    on_success: Callable[[RetryContext, Any], None] | None = None,
    on_failure: Callable[[RetryContext, Exception], None] | None = None,
):
    """
    Decorator for automatic retry with exponential backoff.

    Usage:
        @retry(max_attempts=5, base_delay=1.0, jitter=JitterType.FULL)
        async def fetch_data():
            # ... implementation ...

        @retry(
            max_attempts=3,
            retryable_exceptions=(ConnectionError, TimeoutError),
            non_retryable_exceptions=(ValueError,),
        )
        def process_request():
            # ... implementation ...

    Args:
        max_attempts: Maximum number of attempts (including initial call)
        backoff_strategy: Strategy for calculating delays
        base_delay: Base delay for backoff strategy (seconds)
        max_delay: Maximum delay cap (seconds)
        multiplier: Multiplier for exponential backoff
        jitter: Jitter type to apply to delays
        retryable_exceptions: Tuple of exception types that should trigger retry
        non_retryable_exceptions: Tuple of exception types that should NOT retry
        timeout: Maximum total time for all retries (seconds)
        on_retry: Callback called before each retry
        on_success: Callback called on successful completion
        on_failure: Callback called when all retries exhausted

    Returns:
        Decorated function with retry behavior
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_strategy=backoff_strategy,
        base_delay=base_delay,
        max_delay=max_delay,
        multiplier=multiplier,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
        timeout=timeout,
        on_retry=on_retry,
        on_success=on_success,
        on_failure=on_failure,
    )
    executor = RetryExecutor(config)

    def decorator(func: Callable) -> Callable:
        """Actual decorator that wraps the function."""

        if asyncio.iscoroutinefunction(func):
            # Async function
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await executor.execute_async(func, *args, **kwargs)

            return async_wrapper
        else:
            # Sync function
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return executor.execute_sync(func, *args, **kwargs)

            return sync_wrapper

    return decorator
