"""
Retry backoff strategies.

Defines different strategies for calculating retry delays:
- Exponential backoff: Delays grow exponentially (2^n)
- Linear backoff: Delays grow linearly (n * base_delay)
- Fixed delay: Constant delay between retries
"""

from abc import ABC, abstractmethod
from enum import Enum


class BackoffStrategy(Enum):
    """Types of backoff strategies."""

    FIXED = "fixed"  # Fixed delay
    LINEAR = "linear"  # Linear backoff
    EXPONENTIAL = "exponential"  # Exponential backoff


class RetryStrategy(ABC):
    """Base class for retry strategies."""

    def __init__(
        self,
        max_delay: float | None = None,
    ) -> None:
        """
        Initialize retry strategy.

        Args:
            max_delay: Maximum delay cap (None = no cap)
        """
        self.max_delay = max_delay

    @abstractmethod
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay for a given attempt.

        Args:
            attempt: The retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        pass

    def get_delay(self, attempt: int) -> float:
        """
        Get the delay for an attempt, applying max_delay cap.

        Args:
            attempt: The retry attempt number (0-indexed)

        Returns:
            Delay in seconds (capped at max_delay if set)
        """
        delay = self.calculate_delay(attempt)
        if self.max_delay is not None:
            return min(delay, self.max_delay)
        return delay


class FixedDelayStrategy(RetryStrategy):
    """
    Fixed delay strategy.

    Always returns the same delay regardless of attempt number.
    Useful for simple retry scenarios.

    Formula: delay = base_delay
    """

    def __init__(
        self,
        delay: float = 1.0,
        max_delay: float | None = None,
    ) -> None:
        """
        Initialize fixed delay strategy.

        Args:
            delay: The fixed delay between retries (seconds)
            max_delay: Maximum delay cap (typically not needed for fixed)
        """
        super().__init__(max_delay=max_delay)
        self.delay = delay

    def calculate_delay(self, attempt: int) -> float:
        """
        Return fixed delay.

        Args:
            attempt: Attempt number (unused)

        Returns:
            Fixed delay
        """
        return self.delay


class LinearBackoffStrategy(RetryStrategy):
    """
    Linear backoff strategy.

    Delay increases linearly with attempt number.
    Predictable but can lead to longer waits.

    Formula: delay = base_delay + (attempt * increment)
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float | None = None,
    ) -> None:
        """
        Initialize linear backoff strategy.

        Args:
            base_delay: Initial delay (seconds)
            increment: Amount to add per attempt (seconds)
            max_delay: Maximum delay cap (seconds)
        """
        super().__init__(max_delay=max_delay)
        self.base_delay = base_delay
        self.increment = increment

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate linear backoff delay.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Linear delay: base_delay + (attempt * increment)
        """
        return self.base_delay + (attempt * self.increment)


class ExponentialBackoffStrategy(RetryStrategy):
    """
    Exponential backoff strategy.

    Delay grows exponentially with each attempt.
    Best for network operations and distributed systems.

    Formula: delay = base_delay * (multiplier ^ attempt)

    Example with base_delay=1, multiplier=2:
    - Attempt 0: 1s
    - Attempt 1: 2s
    - Attempt 2: 4s
    - Attempt 3: 8s
    - Attempt 4: 16s
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        multiplier: float = 2.0,
        max_delay: float | None = None,
    ) -> None:
        """
        Initialize exponential backoff strategy.

        Args:
            base_delay: Initial delay (seconds)
            multiplier: Factor to multiply by each attempt (typically 2.0)
            max_delay: Maximum delay cap (seconds)
        """
        super().__init__(max_delay=max_delay)
        self.base_delay = base_delay
        self.multiplier = multiplier

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Exponential delay: base_delay * (multiplier ^ attempt)
        """
        return self.base_delay * (self.multiplier**attempt)


class ExponentialBackoffWithCeiling(RetryStrategy):
    """
    Exponential backoff with a ceiling.

    Like exponential backoff, but delays plateau after reaching max_delay.
    Prevents unbounded growth while maintaining exponential ramp-up.

    Formula:
        delay = min(base_delay * (multiplier ^ attempt), max_delay)
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        multiplier: float = 2.0,
        max_delay: float = 60.0,
    ) -> None:
        """
        Initialize exponential backoff with ceiling.

        Args:
            base_delay: Initial delay (seconds)
            multiplier: Factor to multiply by each attempt
            max_delay: Maximum delay ceiling (seconds)
        """
        super().__init__(max_delay=max_delay)
        self.base_delay = base_delay
        self.multiplier = multiplier

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate exponential delay with ceiling.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Exponential delay capped at max_delay
        """
        return self.base_delay * (self.multiplier**attempt)


def get_retry_strategy(
    strategy: BackoffStrategy,
    base_delay: float = 1.0,
    max_delay: float | None = None,
    **kwargs: float,
) -> RetryStrategy:
    """
    Get a retry strategy instance.

    Args:
        strategy: The backoff strategy to use
        base_delay: Base delay for the strategy
        max_delay: Maximum delay cap
        **kwargs: Additional strategy-specific arguments

    Returns:
        RetryStrategy instance

    Raises:
        ValueError: If strategy is unknown
    """
    if strategy == BackoffStrategy.FIXED:
        return FixedDelayStrategy(delay=base_delay, max_delay=max_delay)

    elif strategy == BackoffStrategy.LINEAR:
        increment = kwargs.get("increment", 1.0)
        return LinearBackoffStrategy(
            base_delay=base_delay,
            increment=increment,
            max_delay=max_delay,
        )

    elif strategy == BackoffStrategy.EXPONENTIAL:
        multiplier = kwargs.get("multiplier", 2.0)
        if max_delay is not None:
            return ExponentialBackoffWithCeiling(
                base_delay=base_delay,
                multiplier=multiplier,
                max_delay=max_delay,
            )
        else:
            return ExponentialBackoffStrategy(
                base_delay=base_delay,
                multiplier=multiplier,
                max_delay=max_delay,
            )

    else:
        raise ValueError(f"Unknown backoff strategy: {strategy}")
