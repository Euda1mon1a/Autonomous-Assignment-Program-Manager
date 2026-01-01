"""
Advanced error handling middleware for the Scheduler MCP server.

This module provides:
- Custom exception hierarchy for MCP-specific errors
- Error handler decorators with automatic error transformation
- Retry logic with exponential backoff and jitter
- Circuit breaker pattern for service resilience
- Structured error responses
- Comprehensive logging and tracing
"""

import asyncio
import functools
import logging
import random
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ParamSpec, TypeVar, cast

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Type variables for generic decorators
P = ParamSpec("P")
T = TypeVar("T")


# ============================================================================
# Custom Exception Classes
# ============================================================================


class MCPErrorCode(str, Enum):
    """Standard error codes for MCP operations."""

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    MISSING_PARAMETER = "MISSING_PARAMETER"

    # Service availability errors
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    API_UNAVAILABLE = "API_UNAVAILABLE"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # Authentication/Authorization
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"

    # Timeout errors
    TIMEOUT = "TIMEOUT"
    OPERATION_TIMEOUT = "OPERATION_TIMEOUT"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # Circuit breaker
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    SERVICE_DEGRADED = "SERVICE_DEGRADED"

    # Generic errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class MCPToolError(Exception):
    """Base exception for all MCP tool errors.

    All MCP-specific exceptions should inherit from this class.
    These exceptions are designed to be safe to expose to clients
    with structured error responses.
    """

    def __init__(
        self,
        message: str,
        error_code: MCPErrorCode = MCPErrorCode.INTERNAL_ERROR,
        details: dict[str, Any] | None = None,
        retry_after: int | None = None,
        correlation_id: str | None = None,
    ):
        """Initialize MCP tool error.

        Args:
            message: User-friendly error message
            error_code: Standardized error code
            details: Additional error context (safe to expose)
            retry_after: Suggested retry delay in seconds
            correlation_id: Unique ID for tracing this error
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.retry_after = retry_after
        self.correlation_id = correlation_id or str(uuid.uuid4())
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured error response.

        Returns:
            Dictionary with error details suitable for API response
        """
        error_dict: dict[str, Any] = {
            "error": True,
            "error_code": self.error_code.value,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.details:
            error_dict["details"] = self.details

        if self.retry_after is not None:
            error_dict["retry_after"] = self.retry_after

        return error_dict


class MCPValidationError(MCPToolError):
    """Input validation failed."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize validation error.

        Args:
            message: Validation error message
            field: Name of field that failed validation
            details: Additional validation context
        """
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            error_code=MCPErrorCode.VALIDATION_ERROR,
            details=error_details,
        )


class MCPServiceUnavailable(MCPToolError):
    """Backend service is unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: str | None = None,
        retry_after: int = 30,
        details: dict[str, Any] | None = None,
    ):
        """Initialize service unavailable error.

        Args:
            message: Error message
            service_name: Name of unavailable service
            retry_after: Suggested retry delay in seconds
            details: Additional context
        """
        error_details = details or {}
        if service_name:
            error_details["service"] = service_name

        super().__init__(
            message=message,
            error_code=MCPErrorCode.SERVICE_UNAVAILABLE,
            details=error_details,
            retry_after=retry_after,
        )


class MCPRateLimitError(MCPToolError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        limit: int | None = None,
        window: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
            limit: Rate limit threshold
            window: Rate limit window in seconds
            details: Additional context
        """
        error_details = details or {}
        if limit is not None:
            error_details["limit"] = limit
        if window is not None:
            error_details["window_seconds"] = window

        super().__init__(
            message=message,
            error_code=MCPErrorCode.RATE_LIMIT_EXCEEDED,
            details=error_details,
            retry_after=retry_after,
        )


class MCPAuthenticationError(MCPToolError):
    """Authentication failed."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        """Initialize authentication error.

        Args:
            message: Error message
            details: Additional context (don't include sensitive data)
        """
        super().__init__(
            message=message,
            error_code=MCPErrorCode.AUTHENTICATION_FAILED,
            details=details,
        )


class MCPTimeoutError(MCPToolError):
    """Operation timed out."""

    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: float | None = None,
        operation: str | None = None,
        retry_after: int = 10,
        details: dict[str, Any] | None = None,
    ):
        """Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: Timeout threshold that was exceeded
            operation: Name of operation that timed out
            retry_after: Suggested retry delay
            details: Additional context
        """
        error_details = details or {}
        if timeout_seconds is not None:
            error_details["timeout_seconds"] = timeout_seconds
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code=MCPErrorCode.TIMEOUT,
            details=error_details,
            retry_after=retry_after,
        )


class MCPCircuitOpenError(MCPToolError):
    """Circuit breaker is open, rejecting requests."""

    def __init__(
        self,
        message: str = "Service circuit breaker open",
        service_name: str | None = None,
        retry_after: int = 60,
        details: dict[str, Any] | None = None,
    ):
        """Initialize circuit open error.

        Args:
            message: Error message
            service_name: Name of service with open circuit
            retry_after: Seconds until circuit may close
            details: Additional context
        """
        error_details = details or {}
        if service_name:
            error_details["service"] = service_name
        error_details["circuit_state"] = "open"

        super().__init__(
            message=message,
            error_code=MCPErrorCode.CIRCUIT_OPEN,
            details=error_details,
            retry_after=retry_after,
        )


# ============================================================================
# Structured Error Response
# ============================================================================


class ErrorResponse(BaseModel):
    """Structured error response model."""

    error: bool = True
    error_code: str
    message: str
    correlation_id: str
    timestamp: str
    details: dict[str, Any] = Field(default_factory=dict)
    retry_after: int | None = None
    stack_trace: str | None = None  # Only populated in debug mode


# ============================================================================
# Retry Logic
# ============================================================================


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add randomness to prevent thundering herd
    retryable_exceptions: tuple[type[Exception], ...] = (
        MCPServiceUnavailable,
        MCPTimeoutError,
        asyncio.TimeoutError,
        ConnectionError,
    )


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """Calculate delay before next retry using exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds before next retry
    """
    # Exponential backoff: base_delay * (exponential_base ^ attempt)
    delay = config.base_delay * (config.exponential_base**attempt)

    # Cap at max delay
    delay = min(delay, config.max_delay)

    # Add jitter to prevent thundering herd
    if config.jitter:
        # Random jitter between 0% and 25% of delay
        jitter = delay * random.uniform(0, 0.25)
        delay += jitter

    return delay


def retry_with_backoff(
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to retry function with exponential backoff.

    Args:
        config: Retry configuration (uses defaults if None)

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            correlation_id = str(uuid.uuid4())
            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    logger.debug(
                        f"Attempt {attempt + 1}/{config.max_attempts} for {func.__name__}",
                        extra={"correlation_id": correlation_id},
                    )
                    result = await func(*args, **kwargs)
                    return result

                except config.retryable_exceptions as e:
                    last_exception = e
                    is_last_attempt = attempt == config.max_attempts - 1

                    if is_last_attempt:
                        logger.error(
                            f"All retry attempts exhausted for {func.__name__}",
                            extra={
                                "correlation_id": correlation_id,
                                "attempts": config.max_attempts,
                            },
                            exc_info=True,
                        )
                        break

                    # Calculate backoff delay
                    delay = calculate_backoff_delay(attempt, config)

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}, "
                        f"retrying in {delay:.2f}s",
                        extra={
                            "correlation_id": correlation_id,
                            "error": str(e),
                            "delay_seconds": delay,
                        },
                    )

                    await asyncio.sleep(delay)

                except Exception:
                    # Non-retryable exception, fail immediately
                    logger.error(
                        f"Non-retryable error in {func.__name__}",
                        extra={"correlation_id": correlation_id},
                        exc_info=True,
                    )
                    raise

            # All retries exhausted, raise last exception
            if last_exception:
                raise last_exception

            # This should never happen, but satisfy type checker
            raise MCPToolError(
                "Retry logic error: no result and no exception",
                correlation_id=correlation_id,
            )

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # For sync functions, just call directly (no retry)
            logger.warning(
                f"retry_with_backoff used on sync function {func.__name__}, "
                "retries not supported for sync functions"
            )
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return cast(Callable[P, T], async_wrapper)
        else:
            return cast(Callable[P, T], sync_wrapper)

    return decorator


# ============================================================================
# Circuit Breaker
# ============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open before closing
    timeout: float = 60.0  # Seconds before moving to half-open
    half_open_max_calls: int = 3  # Max concurrent calls in half-open
    monitored_exceptions: tuple[type[Exception], ...] = (
        MCPServiceUnavailable,
        MCPTimeoutError,
        ConnectionError,
        asyncio.TimeoutError,
    )


@dataclass
class CircuitBreakerState:
    """Runtime state of a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_state_change: float = field(default_factory=time.time)
    half_open_calls: int = 0


class CircuitBreaker:
    """Circuit breaker for service resilience.

    Tracks failure rates and opens circuit after threshold failures,
    preventing cascading failures. Periodically tests recovery in
    half-open state.
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        """Initialize circuit breaker.

        Args:
            name: Unique name for this circuit breaker
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState()
        self._lock = asyncio.Lock()

    async def call(
        self,
        func: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            MCPCircuitOpenError: If circuit is open
            Exception: Any exception raised by function
        """
        async with self._lock:
            await self._update_state()

            # Reject if circuit is open
            if self.state.state == CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker {self.name} is OPEN, rejecting call",
                    extra={
                        "failure_count": self.state.failure_count,
                        "last_failure": self.state.last_failure_time,
                    },
                )
                raise MCPCircuitOpenError(
                    f"Circuit breaker {self.name} is open",
                    service_name=self.name,
                    retry_after=int(self.config.timeout),
                    details={
                        "failure_count": self.state.failure_count,
                        "state": self.state.state.value,
                    },
                )

            # Limit concurrent calls in half-open state
            if self.state.state == CircuitState.HALF_OPEN:
                if self.state.half_open_calls >= self.config.half_open_max_calls:
                    raise MCPCircuitOpenError(
                        f"Circuit breaker {self.name} half-open limit reached",
                        service_name=self.name,
                        retry_after=5,
                    )
                self.state.half_open_calls += 1

        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            await self._on_success()
            return result

        except self.config.monitored_exceptions:
            # Record failure
            await self._on_failure()
            raise

        except Exception as e:
            # Non-monitored exception, don't affect circuit state
            logger.debug(
                f"Circuit breaker {self.name} ignoring non-monitored exception: {type(e).__name__}"
            )
            raise

        finally:
            # Decrement half-open call counter
            if self.state.state == CircuitState.HALF_OPEN:
                async with self._lock:
                    self.state.half_open_calls = max(0, self.state.half_open_calls - 1)

    async def _update_state(self) -> None:
        """Update circuit state based on time and thresholds."""
        now = time.time()

        # Check if should move from OPEN to HALF_OPEN
        if self.state.state == CircuitState.OPEN:
            if (
                self.state.last_failure_time
                and (now - self.state.last_failure_time) >= self.config.timeout
            ):
                logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
                self.state.state = CircuitState.HALF_OPEN
                self.state.success_count = 0
                self.state.half_open_calls = 0
                self.state.last_state_change = now

    async def _on_success(self) -> None:
        """Record successful call."""
        async with self._lock:
            if self.state.state == CircuitState.HALF_OPEN:
                self.state.success_count += 1
                logger.debug(
                    f"Circuit breaker {self.name} success in HALF_OPEN "
                    f"({self.state.success_count}/{self.config.success_threshold})"
                )

                # Close circuit if threshold met
                if self.state.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit breaker {self.name} closing (recovery)")
                    self.state.state = CircuitState.CLOSED
                    self.state.failure_count = 0
                    self.state.success_count = 0
                    self.state.last_state_change = time.time()

            elif self.state.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.state.failure_count = 0

    async def _on_failure(self) -> None:
        """Record failed call."""
        async with self._lock:
            now = time.time()
            self.state.failure_count += 1
            self.state.last_failure_time = now

            logger.warning(
                f"Circuit breaker {self.name} failure "
                f"({self.state.failure_count}/{self.config.failure_threshold})"
            )

            # Open circuit if threshold exceeded
            if (
                self.state.state == CircuitState.CLOSED
                and self.state.failure_count >= self.config.failure_threshold
            ):
                logger.error(f"Circuit breaker {self.name} opening due to failures")
                self.state.state = CircuitState.OPEN
                self.state.last_state_change = now

            # Immediately re-open if failure in half-open
            elif self.state.state == CircuitState.HALF_OPEN:
                logger.error(
                    f"Circuit breaker {self.name} re-opening from HALF_OPEN"
                )
                self.state.state = CircuitState.OPEN
                self.state.success_count = 0
                self.state.last_state_change = now

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state.

        Returns:
            Dictionary with circuit breaker metrics
        """
        return {
            "name": self.name,
            "state": self.state.state.value,
            "failure_count": self.state.failure_count,
            "success_count": self.state.success_count,
            "last_failure_time": self.state.last_failure_time,
            "last_state_change": self.state.last_state_change,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            },
        }


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: CircuitBreakerConfig | None = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker.

    Args:
        name: Circuit breaker name
        config: Configuration (only used for new circuit breakers)

    Returns:
        Circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, dict[str, Any]]:
    """Get state of all circuit breakers.

    Returns:
        Dictionary mapping circuit breaker names to their states
    """
    return {name: cb.get_state() for name, cb in _circuit_breakers.items()}


# ============================================================================
# Error Handler Decorator
# ============================================================================


def mcp_error_handler(
    func: Callable[P, T] | None = None,
    *,
    retry_config: RetryConfig | None = None,
    circuit_breaker_name: str | None = None,
    circuit_breaker_config: CircuitBreakerConfig | None = None,
    log_errors: bool = True,
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for comprehensive MCP error handling.

    Automatically:
    - Catches exceptions and transforms them to MCPToolError
    - Logs errors with correlation IDs
    - Returns structured error responses
    - Optionally applies retry logic
    - Optionally applies circuit breaker pattern

    Args:
        func: Function to decorate (can be None for parameterized decorator)
        retry_config: Optional retry configuration
        circuit_breaker_name: Optional circuit breaker name
        circuit_breaker_config: Optional circuit breaker configuration
        log_errors: Whether to log errors (default: True)

    Returns:
        Decorated function or decorator

    Example:
        @mcp_error_handler
        async def my_tool(...):
            # Tool implementation
            pass

        @mcp_error_handler(retry_config=RetryConfig(max_attempts=5))
        async def my_tool_with_retry(...):
            # Tool implementation with retries
            pass

        @mcp_error_handler(
            circuit_breaker_name="database",
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=3)
        )
        async def my_tool_with_circuit_breaker(...):
            # Tool implementation with circuit breaker
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            correlation_id = str(uuid.uuid4())
            start_time = time.time()

            try:
                # Apply circuit breaker if configured
                if circuit_breaker_name:
                    cb = get_circuit_breaker(
                        circuit_breaker_name,
                        circuit_breaker_config,
                    )
                    result = await cb.call(func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs)

                # Log successful execution
                duration = time.time() - start_time
                logger.debug(
                    f"{func.__name__} completed successfully",
                    extra={
                        "correlation_id": correlation_id,
                        "duration_seconds": duration,
                    },
                )

                return result

            except MCPToolError:
                # Already a structured MCP error, just log and re-raise
                if log_errors:
                    duration = time.time() - start_time
                    logger.warning(
                        f"{func.__name__} failed with MCP error",
                        extra={
                            "correlation_id": correlation_id,
                            "duration_seconds": duration,
                        },
                        exc_info=True,
                    )
                raise

            except ValueError as e:
                # Convert ValueError to validation error
                if log_errors:
                    logger.warning(
                        f"{func.__name__} failed with validation error",
                        extra={"correlation_id": correlation_id},
                        exc_info=True,
                    )
                raise MCPValidationError(
                    message=str(e),
                    details={"original_error": type(e).__name__},
                ) from e

            except asyncio.TimeoutError as e:
                # Convert asyncio timeout to MCP timeout error
                if log_errors:
                    logger.error(
                        f"{func.__name__} timed out",
                        extra={"correlation_id": correlation_id},
                        exc_info=True,
                    )
                error = MCPTimeoutError(
                    message=f"Operation {func.__name__} timed out",
                    operation=func.__name__,
                )
                error.correlation_id = correlation_id
                raise error from e

            except ConnectionError as e:
                # Convert connection errors to service unavailable
                if log_errors:
                    logger.error(
                        f"{func.__name__} connection error",
                        extra={"correlation_id": correlation_id},
                        exc_info=True,
                    )
                raise MCPServiceUnavailable(
                    message="Service connection failed",
                    details={
                        "original_error": str(e),
                        "error_type": type(e).__name__,
                    },
                ) from e

            except Exception as e:
                # Catch-all for unexpected errors
                if log_errors:
                    logger.error(
                        f"{func.__name__} unexpected error",
                        extra={"correlation_id": correlation_id},
                        exc_info=True,
                    )

                # Don't leak internal error details
                raise MCPToolError(
                    message="An unexpected error occurred",
                    error_code=MCPErrorCode.INTERNAL_ERROR,
                    details={
                        "error_type": type(e).__name__,
                        # Only include message if it's safe
                        "error_message": str(e) if not _is_sensitive_error(e) else None,
                    },
                    correlation_id=correlation_id,
                ) from e

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Similar logic for sync functions
            correlation_id = str(uuid.uuid4())

            try:
                return func(*args, **kwargs)

            except MCPToolError:
                raise

            except ValueError as e:
                raise MCPValidationError(
                    message=str(e),
                    details={"original_error": type(e).__name__},
                ) from e

            except Exception as e:
                if log_errors:
                    logger.error(
                        f"{func.__name__} unexpected error",
                        extra={"correlation_id": correlation_id},
                        exc_info=True,
                    )
                raise MCPToolError(
                    message="An unexpected error occurred",
                    error_code=MCPErrorCode.INTERNAL_ERROR,
                    details={"error_type": type(e).__name__},
                    correlation_id=correlation_id,
                ) from e

        # Apply retry decorator if configured
        if retry_config:
            if asyncio.iscoroutinefunction(func):
                wrapper = retry_with_backoff(retry_config)(async_wrapper)
            else:
                wrapper = sync_wrapper
        else:
            wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return cast(Callable[P, T], wrapper)

    # Support both @mcp_error_handler and @mcp_error_handler(...)
    if func is None:
        return decorator
    else:
        return decorator(func)


def _is_sensitive_error(error: Exception) -> bool:
    """Check if error message might contain sensitive information.

    Args:
        error: Exception to check

    Returns:
        True if error might contain sensitive data
    """
    error_msg = str(error).lower()
    sensitive_keywords = [
        "password",
        "token",
        "secret",
        "key",
        "credential",
        "auth",
        "ssn",
        "social security",
        "dob",
        "date of birth",
    ]

    return any(keyword in error_msg for keyword in sensitive_keywords)


# ============================================================================
# Metrics and Monitoring
# ============================================================================


@dataclass
class ErrorMetrics:
    """Error metrics for monitoring."""

    total_errors: int = 0
    errors_by_code: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_tool: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_error_time: float | None = None
    error_rate_per_minute: float = 0.0


_error_metrics = ErrorMetrics()


def record_error(
    error_code: MCPErrorCode,
    tool_name: str | None = None,
) -> None:
    """Record error for metrics tracking.

    Args:
        error_code: Error code that occurred
        tool_name: Name of tool where error occurred
    """
    _error_metrics.total_errors += 1
    _error_metrics.errors_by_code[error_code.value] += 1
    if tool_name:
        _error_metrics.errors_by_tool[tool_name] += 1
    _error_metrics.last_error_time = time.time()


def get_error_metrics() -> dict[str, Any]:
    """Get current error metrics.

    Returns:
        Dictionary with error metrics
    """
    return {
        "total_errors": _error_metrics.total_errors,
        "errors_by_code": dict(_error_metrics.errors_by_code),
        "errors_by_tool": dict(_error_metrics.errors_by_tool),
        "last_error_time": _error_metrics.last_error_time,
        "circuit_breakers": get_all_circuit_breakers(),
    }


def reset_error_metrics() -> None:
    """Reset error metrics (useful for testing)."""
    global _error_metrics
    _error_metrics = ErrorMetrics()
