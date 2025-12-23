"""
Jitter implementations for retry backoff.

Jitter adds randomness to retry delays to prevent thundering herd problems
when multiple clients retry simultaneously.

Implementations:
- Full Jitter: Random value between 0 and calculated delay
- Equal Jitter: Half fixed delay + half random
- Decorrelated Jitter: Each delay depends on previous delay (AWS recommendation)
"""

import random
from abc import ABC, abstractmethod
from enum import Enum


class JitterType(Enum):
    """Types of jitter strategies."""

    NONE = "none"  # No jitter (deterministic delays)
    FULL = "full"  # Full jitter (0 to delay)
    EQUAL = "equal"  # Equal jitter (delay/2 + random(0, delay/2))
    DECORRELATED = "decorrelated"  # Decorrelated jitter (AWS-style)


class JitterStrategy(ABC):
    """Base class for jitter strategies."""

    @abstractmethod
    def apply(self, delay: float, attempt: int, previous_delay: float = 0.0) -> float:
        """
        Apply jitter to a delay value.

        Args:
            delay: The base delay to apply jitter to
            attempt: The current retry attempt number (0-indexed)
            previous_delay: The previous actual delay used (for decorrelated)

        Returns:
            The jittered delay value
        """
        pass


class NoJitter(JitterStrategy):
    """No jitter - returns delay unchanged."""

    def apply(self, delay: float, attempt: int, previous_delay: float = 0.0) -> float:
        """Return delay unchanged."""
        return delay


class FullJitter(JitterStrategy):
    """
    Full jitter strategy.

    Returns a random value between 0 and the calculated delay.
    Maximum distribution of retry times.

    Formula: random(0, delay)
    """

    def apply(self, delay: float, attempt: int, previous_delay: float = 0.0) -> float:
        """
        Apply full jitter.

        Args:
            delay: The base delay
            attempt: Current attempt number (unused)
            previous_delay: Previous delay (unused)

        Returns:
            Random value between 0 and delay
        """
        return random.uniform(0, delay)


class EqualJitter(JitterStrategy):
    """
    Equal jitter strategy.

    Returns half the delay plus a random value between 0 and the other half.
    Balances predictability with randomization.

    Formula: delay/2 + random(0, delay/2)
    """

    def apply(self, delay: float, attempt: int, previous_delay: float = 0.0) -> float:
        """
        Apply equal jitter.

        Args:
            delay: The base delay
            attempt: Current attempt number (unused)
            previous_delay: Previous delay (unused)

        Returns:
            Half delay plus random half
        """
        half = delay / 2
        return half + random.uniform(0, half)


class DecorrelatedJitter(JitterStrategy):
    """
    Decorrelated jitter strategy (AWS recommendation).

    Each delay is calculated based on the previous delay, creating
    decorrelation between successive retry attempts.

    Formula: random(base_delay, previous_delay * 3)

    This is the AWS-recommended approach for exponential backoff with jitter.

    Reference:
        https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    """

    def __init__(self, base_delay: float = 1.0):
        """
        Initialize decorrelated jitter.

        Args:
            base_delay: The minimum delay to use as lower bound
        """
        self.base_delay = base_delay

    def apply(self, delay: float, attempt: int, previous_delay: float = 0.0) -> float:
        """
        Apply decorrelated jitter.

        Args:
            delay: The base delay (used only if previous_delay is 0)
            attempt: Current attempt number (unused)
            previous_delay: The previous actual delay used

        Returns:
            Random value between base_delay and previous_delay * 3
        """
        if previous_delay == 0.0:
            # First attempt - use base delay with some jitter
            return random.uniform(self.base_delay, delay)

        # Subsequent attempts - decorrelate from previous delay
        upper_bound = previous_delay * 3
        return random.uniform(self.base_delay, upper_bound)


def get_jitter_strategy(jitter_type: JitterType, **kwargs) -> JitterStrategy:
    """
    Get a jitter strategy instance.

    Args:
        jitter_type: The type of jitter to use
        **kwargs: Additional arguments for specific jitter strategies

    Returns:
        JitterStrategy instance

    Raises:
        ValueError: If jitter_type is unknown
    """
    if jitter_type == JitterType.NONE:
        return NoJitter()
    elif jitter_type == JitterType.FULL:
        return FullJitter()
    elif jitter_type == JitterType.EQUAL:
        return EqualJitter()
    elif jitter_type == JitterType.DECORRELATED:
        base_delay = kwargs.get("base_delay", 1.0)
        return DecorrelatedJitter(base_delay=base_delay)
    else:
        raise ValueError(f"Unknown jitter type: {jitter_type}")
