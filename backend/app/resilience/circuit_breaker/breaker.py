"""
Circuit Breaker Implementation.

Provides fail-fast behavior and automatic recovery for resilience:

1. Protects services from cascading failures
2. Provides fallback mechanisms
3. Automatically attempts recovery
4. Integrates with metrics and monitoring

Based on the Netflix Hystrix pattern and the Release It! book by Michael Nygard.
"""

import asyncio
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Any, TypeVar

from app.resilience.circuit_breaker.states import CircuitState, StateMachine

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""

    pass


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit is open and request is rejected."""

    pass


class CircuitBreakerTimeoutError(CircuitBreakerError):
    """Raised when a call times out."""

    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    name: str
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    call_timeout_seconds: float | None = None
    half_open_max_calls: int = 3
    excluded_exceptions: tuple[type[Exception], ...] = ()
    fallback_function: Callable | None = None


class CircuitBreaker:
    """
    Circuit breaker for protecting service calls.

    Implements the circuit breaker pattern:
    - Monitors calls for failures
    - Opens circuit when threshold exceeded
    - Attempts recovery after timeout
    - Provides fallback mechanisms

    Example:
        breaker = CircuitBreaker("database", failure_threshold=5)

        # Use as context manager
        with breaker:
            result = risky_database_call()

        # Use with async
        async with breaker:
            result = await risky_async_call()

        # Use as decorator (via registry)
        @circuit_breaker("external_api")
        async def call_api():
            return await api_client.get("/data")
    """

    def __init__(self, config: CircuitBreakerConfig) -> None:
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.name = config.name
        self.state_machine = StateMachine(
            failure_threshold=config.failure_threshold,
            success_threshold=config.success_threshold,
            timeout_seconds=config.timeout_seconds,
            half_open_max_calls=config.half_open_max_calls,
        )
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{self.name}' initialized: "
            f"failure_threshold={config.failure_threshold}, "
            f"timeout={config.timeout_seconds}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state_machine.current_state

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a synchronous function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitOpenError: If circuit is open
            CircuitBreakerTimeoutError: If call times out
        """
        if not self.state_machine.should_allow_request():
            self.state_machine.record_rejection()
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, request rejected")

            # Try fallback
            if self.config.fallback_function:
                logger.info(f"Using fallback for '{self.name}'")
                return self.config.fallback_function(*args, **kwargs)

            raise CircuitOpenError(
                f"Circuit breaker '{self.name}' is OPEN. Service is unavailable."
            )

            # If half-open, track in-flight calls
        if self.state == CircuitState.HALF_OPEN:
            self.state_machine.half_open_calls_in_flight += 1

        try:
            # Execute with timeout if configured
            if self.config.call_timeout_seconds:
                import signal

                def timeout_handler(signum, frame):
                    raise CircuitBreakerTimeoutError(
                        f"Call timed out after {self.config.call_timeout_seconds}s"
                    )

                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.config.call_timeout_seconds))
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)
            else:
                result = func(*args, **kwargs)

                # Success
            self.state_machine.record_success()
            return result

        except Exception as e:
            # Check if exception should be excluded from failure count
            if isinstance(e, self.config.excluded_exceptions):
                logger.debug(
                    f"Exception {type(e).__name__} excluded from failure count"
                )
                raise

                # Record failure
            self.state_machine.record_failure()
            logger.error(
                f"Circuit breaker '{self.name}' recorded failure: {type(e).__name__}"
            )

            # Try fallback
            if self.config.fallback_function:
                logger.info(f"Using fallback for '{self.name}' after error")
                try:
                    return self.config.fallback_function(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback also failed: {type(fallback_error).__name__}"
                    )

            raise

        finally:
            if self.state == CircuitState.HALF_OPEN:
                self.state_machine.half_open_calls_in_flight -= 1

    async def call_async(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """
        Execute an async function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitOpenError: If circuit is open
            CircuitBreakerTimeoutError: If call times out
        """
        async with self._lock:
            should_allow = self.state_machine.should_allow_request()

        if not should_allow:
            self.state_machine.record_rejection()
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, request rejected")

            # Try fallback
            if self.config.fallback_function:
                logger.info(f"Using fallback for '{self.name}'")
                if asyncio.iscoroutinefunction(self.config.fallback_function):
                    return await self.config.fallback_function(*args, **kwargs)
                return self.config.fallback_function(*args, **kwargs)

            raise CircuitOpenError(
                f"Circuit breaker '{self.name}' is OPEN. Service is unavailable."
            )

            # If half-open, track in-flight calls
        if self.state == CircuitState.HALF_OPEN:
            self.state_machine.half_open_calls_in_flight += 1

        try:
            # Execute with timeout if configured
            if self.config.call_timeout_seconds:
                try:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.call_timeout_seconds,
                    )
                except TimeoutError:
                    raise CircuitBreakerTimeoutError(
                        f"Call timed out after {self.config.call_timeout_seconds}s"
                    )
            else:
                result = await func(*args, **kwargs)

                # Success
            async with self._lock:
                self.state_machine.record_success()
            return result

        except Exception as e:
            # Check if exception should be excluded from failure count
            if isinstance(e, self.config.excluded_exceptions):
                logger.debug(
                    f"Exception {type(e).__name__} excluded from failure count"
                )
                raise

                # Record failure
            async with self._lock:
                self.state_machine.record_failure()

            logger.error(
                f"Circuit breaker '{self.name}' recorded failure: {type(e).__name__}"
            )

            # Try fallback
            if self.config.fallback_function:
                logger.info(f"Using fallback for '{self.name}' after error")
                try:
                    if asyncio.iscoroutinefunction(self.config.fallback_function):
                        return await self.config.fallback_function(*args, **kwargs)
                    return self.config.fallback_function(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback also failed: {type(fallback_error).__name__}"
                    )

            raise

        finally:
            if self.state == CircuitState.HALF_OPEN:
                self.state_machine.half_open_calls_in_flight -= 1

    @contextmanager
    def __call__(self):
        """
        Context manager for synchronous code.

        Usage:
            with breaker():
                risky_operation()
        """
        if not self.state_machine.should_allow_request():
            self.state_machine.record_rejection()
            raise CircuitOpenError(f"Circuit breaker '{self.name}' is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            self.state_machine.half_open_calls_in_flight += 1

        try:
            yield
            self.state_machine.record_success()
        except Exception as e:
            if not isinstance(e, self.config.excluded_exceptions):
                self.state_machine.record_failure()
            raise
        finally:
            if self.state == CircuitState.HALF_OPEN:
                self.state_machine.half_open_calls_in_flight -= 1

    @asynccontextmanager
    async def async_call(self):
        """
        Async context manager.

        Usage:
            async with breaker.async_call():
                await risky_async_operation()
        """
        async with self._lock:
            should_allow = self.state_machine.should_allow_request()

        if not should_allow:
            self.state_machine.record_rejection()
            raise CircuitOpenError(f"Circuit breaker '{self.name}' is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            self.state_machine.half_open_calls_in_flight += 1

        try:
            yield
            async with self._lock:
                self.state_machine.record_success()
        except Exception as e:
            if not isinstance(e, self.config.excluded_exceptions):
                async with self._lock:
                    self.state_machine.record_failure()
            raise
        finally:
            if self.state == CircuitState.HALF_OPEN:
                self.state_machine.half_open_calls_in_flight -= 1

    def open(self, reason: str = "Manual override") -> None:
        """
        Manually open the circuit.

        Args:
            reason: Reason for manual open
        """
        self.state_machine.force_open(reason)

    def close(self, reason: str = "Manual override") -> None:
        """
        Manually close the circuit.

        Args:
            reason: Reason for manual close
        """
        self.state_machine.force_closed(reason)

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self.state_machine.reset()

    def get_status(self) -> dict:
        """
        Get current status and metrics.

        Returns:
            Dictionary with circuit breaker status
        """
        return {
            "name": self.name,
            **self.state_machine.get_status(),
        }
