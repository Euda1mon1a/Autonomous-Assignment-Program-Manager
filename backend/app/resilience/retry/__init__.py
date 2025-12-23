"""
Retry mechanisms with exponential backoff and jitter.

This package provides comprehensive retry functionality for handling transient failures:

Core Components:
- Retry decorator with async/sync support
- Multiple backoff strategies (exponential, linear, fixed)
- Jitter implementations (full, equal, decorrelated)
- Exception filtering (retryable vs non-retryable)
- Callbacks for observability
- Timeout support
- Retry context tracking

Backoff Strategies:
1. Exponential: Delays grow exponentially (1s, 2s, 4s, 8s, ...)
2. Linear: Delays grow linearly (1s, 2s, 3s, 4s, ...)
3. Fixed: Constant delay between retries (1s, 1s, 1s, ...)

Jitter Types:
1. Full: Random value between 0 and delay (AWS recommendation)
2. Equal: Half fixed + half random
3. Decorrelated: Each delay depends on previous (AWS advanced)
4. None: No jitter (deterministic)

Usage Examples:

    Basic exponential backoff with full jitter:
    >>> from app.resilience.retry import retry, JitterType
    >>>
    >>> @retry(max_attempts=5, base_delay=1.0, jitter=JitterType.FULL)
    >>> async def fetch_data():
    ...     # Implementation that may fail transiently
    ...     pass

    Custom exception handling:
    >>> from app.resilience.retry import retry, BackoffStrategy
    >>>
    >>> @retry(
    ...     max_attempts=3,
    ...     backoff_strategy=BackoffStrategy.LINEAR,
    ...     retryable_exceptions=(ConnectionError, TimeoutError),
    ...     non_retryable_exceptions=(ValueError, KeyError),
    ... )
    >>> def process_request():
    ...     # Implementation
    ...     pass

    With callbacks for observability:
    >>> def on_retry_callback(ctx, exc, delay):
    ...     print(f"Retry {ctx.attempt_count}: {exc}, waiting {delay}s")
    >>>
    >>> @retry(max_attempts=5, on_retry=on_retry_callback)
    >>> async def critical_operation():
    ...     # Implementation
    ...     pass

    Programmatic retry without decorator:
    >>> from app.resilience.retry import RetryExecutor, RetryConfig
    >>>
    >>> config = RetryConfig(max_attempts=5, base_delay=1.0)
    >>> executor = RetryExecutor(config)
    >>> result = await executor.execute_async(some_async_function, arg1, arg2)
"""

# Core decorator and executor
# Context tracking
from app.resilience.retry.context import (
    RetryAttempt,
    RetryContext,
)
from app.resilience.retry.decorator import (
    RetryConfig,
    RetryExecutor,
    retry,
)

# Exceptions
from app.resilience.retry.exceptions import (
    InvalidRetryConfigError,
    MaxRetriesExceeded,
    NonRetryableError,
    RetryError,
    RetryTimeoutError,
)

# Jitter strategies
from app.resilience.retry.jitter import (
    DecorrelatedJitter,
    EqualJitter,
    FullJitter,
    JitterStrategy,
    JitterType,
    NoJitter,
    get_jitter_strategy,
)

# Backoff strategies
from app.resilience.retry.strategies import (
    BackoffStrategy,
    ExponentialBackoffStrategy,
    ExponentialBackoffWithCeiling,
    FixedDelayStrategy,
    LinearBackoffStrategy,
    RetryStrategy,
    get_retry_strategy,
)

__all__ = [
    # Main decorator and executor
    "retry",
    "RetryExecutor",
    "RetryConfig",
    # Context tracking
    "RetryContext",
    "RetryAttempt",
    # Exceptions
    "RetryError",
    "MaxRetriesExceeded",
    "NonRetryableError",
    "RetryTimeoutError",
    "InvalidRetryConfigError",
    # Backoff strategies
    "BackoffStrategy",
    "RetryStrategy",
    "FixedDelayStrategy",
    "LinearBackoffStrategy",
    "ExponentialBackoffStrategy",
    "ExponentialBackoffWithCeiling",
    "get_retry_strategy",
    # Jitter strategies
    "JitterType",
    "JitterStrategy",
    "NoJitter",
    "FullJitter",
    "EqualJitter",
    "DecorrelatedJitter",
    "get_jitter_strategy",
]
