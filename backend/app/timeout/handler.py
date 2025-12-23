"""
Core timeout handling logic.

Provides timeout context managers and utilities for graceful cancellation
of async operations.
"""

import asyncio
import builtins
import logging
import time
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable for tracking timeout state
timeout_ctx: ContextVar[float | None] = ContextVar("timeout_remaining", default=None)
timeout_start_ctx: ContextVar[float | None] = ContextVar("timeout_start", default=None)


class TimeoutError(Exception):
    """
    Request timeout error.

    Raised when an operation exceeds its allocated time limit.
    This is a user-friendly exception safe to expose in API responses.
    """

    def __init__(self, message: str = "Request timeout", timeout: float = 0):
        """
        Initialize timeout error.

        Args:
            message: User-friendly error message
            timeout: The timeout value that was exceeded (in seconds)
        """
        self.message = message
        self.timeout = timeout
        super().__init__(message)


class TimeoutHandler:
    """
    Context manager for handling async operation timeouts.

    Features:
    - Async timeout support using asyncio.wait_for
    - Graceful cancellation of operations
    - Timeout tracking and remaining time calculation
    - Nested timeout support (uses minimum timeout)

    Usage:
        async with TimeoutHandler(30.0) as handler:
            result = await some_async_operation()
            remaining = handler.get_remaining_time()
    """

    def __init__(self, timeout: float, error_message: str | None = None):
        """
        Initialize timeout handler.

        Args:
            timeout: Timeout in seconds
            error_message: Custom error message for timeout exception
        """
        self.timeout = timeout
        self.error_message = (
            error_message or f"Operation exceeded timeout of {timeout}s"
        )
        self.start_time: float | None = None
        self._task: asyncio.Task | None = None
        self._token_remaining = None
        self._token_start = None

    async def __aenter__(self):
        """Enter async context - start timeout tracking."""
        self.start_time = time.monotonic()

        # Check if there's already a timeout set (nested timeout)
        existing_remaining = timeout_ctx.get()
        if existing_remaining is not None:
            # Use the minimum of existing and new timeout
            self.timeout = min(self.timeout, existing_remaining)
            logger.debug(f"Nested timeout detected, using minimum: {self.timeout}s")

        # Store timeout in context
        self._token_remaining = timeout_ctx.set(self.timeout)
        self._token_start = timeout_start_ctx.set(self.start_time)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - clean up timeout tracking."""
        # Reset context variables
        if self._token_remaining:
            timeout_ctx.reset(self._token_remaining)
        if self._token_start:
            timeout_start_ctx.reset(self._token_start)

        # Handle asyncio.CancelledError as timeout
        if exc_type is asyncio.CancelledError:
            logger.warning(
                f"Operation cancelled (likely timeout): {self.error_message}"
            )
            raise TimeoutError(self.error_message, self.timeout) from exc_val

        # Handle asyncio.TimeoutError
        if exc_type is asyncio.TimeoutError:
            logger.warning(f"Operation timed out: {self.error_message}")
            raise TimeoutError(self.error_message, self.timeout) from exc_val

        return False

    def get_remaining_time(self) -> float:
        """
        Get remaining time before timeout.

        Returns:
            float: Remaining seconds, or 0 if timeout exceeded
        """
        if self.start_time is None:
            return self.timeout

        elapsed = time.monotonic() - self.start_time
        remaining = max(0, self.timeout - elapsed)
        return remaining

    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since timeout started.

        Returns:
            float: Elapsed seconds
        """
        if self.start_time is None:
            return 0
        return time.monotonic() - self.start_time

    def check_timeout(self) -> None:
        """
        Check if timeout has been exceeded and raise if so.

        Raises:
            TimeoutError: If timeout has been exceeded
        """
        if self.get_remaining_time() <= 0:
            raise TimeoutError(self.error_message, self.timeout)


def get_timeout_remaining() -> float | None:
    """
    Get remaining timeout from context.

    Returns:
        Optional[float]: Remaining timeout in seconds, or None if no timeout set
    """
    timeout = timeout_ctx.get()
    start = timeout_start_ctx.get()

    if timeout is None or start is None:
        return None

    elapsed = time.monotonic() - start
    remaining = max(0, timeout - elapsed)
    return remaining


def get_timeout_elapsed() -> float | None:
    """
    Get elapsed time from timeout start.

    Returns:
        Optional[float]: Elapsed time in seconds, or None if no timeout set
    """
    start = timeout_start_ctx.get()
    if start is None:
        return None

    return time.monotonic() - start


async def with_timeout_wrapper(coro, timeout: float, error_message: str | None = None):
    """
    Wrap a coroutine with timeout handling.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        error_message: Custom error message

    Returns:
        Result of the coroutine

    Raises:
        TimeoutError: If operation exceeds timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except builtins.TimeoutError as e:
        msg = error_message or f"Operation exceeded timeout of {timeout}s"
        logger.warning(f"Timeout: {msg}")
        raise TimeoutError(msg, timeout) from e
    except asyncio.CancelledError as e:
        msg = error_message or f"Operation cancelled (timeout: {timeout}s)"
        logger.warning(f"Cancellation: {msg}")
        raise TimeoutError(msg, timeout) from e
