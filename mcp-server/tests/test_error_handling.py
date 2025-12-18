"""
Tests for MCP error handling middleware.

This module tests the error handling, retry logic, circuit breaker,
and structured error response functionality.
"""

import asyncio
import pytest
import time
from typing import Any

from scheduler_mcp.error_handling import (
    # Exception classes
    MCPToolError,
    MCPValidationError,
    MCPServiceUnavailable,
    MCPRateLimitError,
    MCPAuthenticationError,
    MCPTimeoutError,
    MCPCircuitOpenError,
    MCPErrorCode,
    # Decorators and utilities
    mcp_error_handler,
    retry_with_backoff,
    RetryConfig,
    # Circuit breaker
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    get_circuit_breaker,
    get_all_circuit_breakers,
    # Metrics
    get_error_metrics,
    reset_error_metrics,
    record_error,
)


# ============================================================================
# Exception Tests
# ============================================================================


class TestMCPExceptions:
    """Test MCP exception classes."""

    def test_mcp_tool_error_basic(self):
        """Test basic MCPToolError creation."""
        error = MCPToolError(
            message="Test error",
            error_code=MCPErrorCode.INTERNAL_ERROR,
        )

        assert error.message == "Test error"
        assert error.error_code == MCPErrorCode.INTERNAL_ERROR
        assert error.details == {}
        assert error.retry_after is None
        assert error.correlation_id is not None

    def test_mcp_tool_error_to_dict(self):
        """Test MCPToolError.to_dict() serialization."""
        error = MCPToolError(
            message="Test error",
            error_code=MCPErrorCode.VALIDATION_ERROR,
            details={"field": "email"},
            retry_after=30,
        )

        error_dict = error.to_dict()

        assert error_dict["error"] is True
        assert error_dict["error_code"] == "VALIDATION_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["details"]["field"] == "email"
        assert error_dict["retry_after"] == 30
        assert "correlation_id" in error_dict
        assert "timestamp" in error_dict

    def test_validation_error(self):
        """Test MCPValidationError."""
        error = MCPValidationError(
            message="Invalid email format",
            field="email",
        )

        assert error.message == "Invalid email format"
        assert error.error_code == MCPErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "email"

    def test_service_unavailable_error(self):
        """Test MCPServiceUnavailable."""
        error = MCPServiceUnavailable(
            service_name="database",
            retry_after=60,
        )

        assert error.error_code == MCPErrorCode.SERVICE_UNAVAILABLE
        assert error.details["service"] == "database"
        assert error.retry_after == 60

    def test_rate_limit_error(self):
        """Test MCPRateLimitError."""
        error = MCPRateLimitError(
            limit=100,
            window=60,
            retry_after=30,
        )

        assert error.error_code == MCPErrorCode.RATE_LIMIT_EXCEEDED
        assert error.details["limit"] == 100
        assert error.details["window_seconds"] == 60
        assert error.retry_after == 30

    def test_authentication_error(self):
        """Test MCPAuthenticationError."""
        error = MCPAuthenticationError()

        assert error.error_code == MCPErrorCode.AUTHENTICATION_FAILED
        assert "Authentication failed" in error.message

    def test_timeout_error(self):
        """Test MCPTimeoutError."""
        error = MCPTimeoutError(
            timeout_seconds=30.0,
            operation="database_query",
        )

        assert error.error_code == MCPErrorCode.TIMEOUT
        assert error.details["timeout_seconds"] == 30.0
        assert error.details["operation"] == "database_query"

    def test_circuit_open_error(self):
        """Test MCPCircuitOpenError."""
        error = MCPCircuitOpenError(
            service_name="api",
            retry_after=60,
        )

        assert error.error_code == MCPErrorCode.CIRCUIT_OPEN
        assert error.details["service"] == "api"
        assert error.details["circuit_state"] == "open"
        assert error.retry_after == 60


# ============================================================================
# Retry Logic Tests
# ============================================================================


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        call_count = 0

        @retry_with_backoff(RetryConfig(max_attempts=3))
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful execution after some failures."""
        call_count = 0

        @retry_with_backoff(
            RetryConfig(
                max_attempts=3,
                base_delay=0.01,  # Fast for testing
            )
        )
        async def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise MCPServiceUnavailable("Service down")
            return "success"

        result = await eventually_successful()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test all retry attempts exhausted."""
        call_count = 0

        @retry_with_backoff(
            RetryConfig(
                max_attempts=3,
                base_delay=0.01,
            )
        )
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise MCPServiceUnavailable("Service down")

        with pytest.raises(MCPServiceUnavailable):
            await always_fails()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self):
        """Test non-retryable exception fails immediately."""
        call_count = 0

        @retry_with_backoff(RetryConfig(max_attempts=3))
        async def raises_validation_error():
            nonlocal call_count
            call_count += 1
            raise MCPValidationError("Invalid input")

        with pytest.raises(MCPValidationError):
            await raises_validation_error()

        # Should not retry validation errors
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_backoff_timing(self):
        """Test exponential backoff delays."""
        call_times = []

        @retry_with_backoff(
            RetryConfig(
                max_attempts=3,
                base_delay=0.1,
                exponential_base=2.0,
                jitter=False,  # Disable jitter for predictable timing
            )
        )
        async def always_fails():
            call_times.append(time.time())
            raise MCPTimeoutError()

        with pytest.raises(MCPTimeoutError):
            await always_fails()

        # Verify increasing delays (approximately)
        # Attempt 0: immediate
        # Attempt 1: ~0.1s delay (base_delay * 2^0)
        # Attempt 2: ~0.2s delay (base_delay * 2^1)
        assert len(call_times) == 3

        delay_1 = call_times[1] - call_times[0]
        delay_2 = call_times[2] - call_times[1]

        # Allow some tolerance for timing
        assert 0.08 <= delay_1 <= 0.15
        assert 0.18 <= delay_2 <= 0.25


# ============================================================================
# Circuit Breaker Tests
# ============================================================================


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker(
            "test_service",
            CircuitBreakerConfig(failure_threshold=3),
        )

        async def successful_call():
            return "success"

        result = await cb.call(successful_call)
        assert result == "success"
        assert cb.state.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(
            "test_service",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout=1.0,
            ),
        )

        async def failing_call():
            raise MCPServiceUnavailable("Service down")

        # First 3 failures should open circuit
        for i in range(3):
            with pytest.raises(MCPServiceUnavailable):
                await cb.call(failing_call)

        # Circuit should now be open
        assert cb.state.state == CircuitState.OPEN

        # Next call should be rejected immediately
        with pytest.raises(MCPCircuitOpenError):
            await cb.call(failing_call)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery via half-open state."""
        cb = CircuitBreaker(
            "test_service",
            CircuitBreakerConfig(
                failure_threshold=2,
                success_threshold=2,
                timeout=0.1,  # Short timeout for testing
            ),
        )

        call_count = 0

        async def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise MCPServiceUnavailable("Service down")
            return "success"

        # Trigger failures to open circuit
        for i in range(2):
            with pytest.raises(MCPServiceUnavailable):
                await cb.call(sometimes_fails)

        assert cb.state.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Circuit should move to half-open and allow calls
        # Need 2 successes to close
        result1 = await cb.call(lambda: asyncio.sleep(0))
        assert cb.state.state == CircuitState.HALF_OPEN

        result2 = await cb.call(lambda: asyncio.sleep(0))
        assert cb.state.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_reopens_from_half_open(self):
        """Test circuit breaker re-opens if failure in half-open."""
        cb = CircuitBreaker(
            "test_service",
            CircuitBreakerConfig(
                failure_threshold=2,
                timeout=0.1,
            ),
        )

        async def failing_call():
            raise MCPServiceUnavailable("Service down")

        # Open the circuit
        for i in range(2):
            with pytest.raises(MCPServiceUnavailable):
                await cb.call(failing_call)

        assert cb.state.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Try in half-open state, should fail and re-open
        with pytest.raises(MCPServiceUnavailable):
            await cb.call(failing_call)

        assert cb.state.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_get_state(self):
        """Test getting circuit breaker state."""
        cb = CircuitBreaker(
            "test_service",
            CircuitBreakerConfig(failure_threshold=5),
        )

        state = cb.get_state()

        assert state["name"] == "test_service"
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert "config" in state

    def test_get_circuit_breaker(self):
        """Test global circuit breaker registry."""
        cb1 = get_circuit_breaker("service1")
        cb2 = get_circuit_breaker("service1")

        # Should return same instance
        assert cb1 is cb2

        cb3 = get_circuit_breaker("service2")
        # Should be different instance
        assert cb3 is not cb1

    def test_get_all_circuit_breakers(self):
        """Test getting all circuit breaker states."""
        # Create some circuit breakers
        get_circuit_breaker("service_a")
        get_circuit_breaker("service_b")

        states = get_all_circuit_breakers()

        assert "service_a" in states
        assert "service_b" in states
        assert states["service_a"]["state"] == "closed"


# ============================================================================
# Error Handler Decorator Tests
# ============================================================================


class TestErrorHandlerDecorator:
    """Test mcp_error_handler decorator."""

    @pytest.mark.asyncio
    async def test_error_handler_success(self):
        """Test decorator with successful execution."""

        @mcp_error_handler
        async def successful_tool():
            return {"result": "success"}

        result = await successful_tool()
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_error_handler_mcp_error_passthrough(self):
        """Test decorator passes through MCPToolError."""

        @mcp_error_handler
        async def raises_mcp_error():
            raise MCPValidationError("Invalid input")

        with pytest.raises(MCPValidationError) as exc_info:
            await raises_mcp_error()

        assert "Invalid input" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handler_value_error_conversion(self):
        """Test decorator converts ValueError to MCPValidationError."""

        @mcp_error_handler
        async def raises_value_error():
            raise ValueError("Invalid parameter")

        with pytest.raises(MCPValidationError) as exc_info:
            await raises_value_error()

        assert "Invalid parameter" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handler_timeout_conversion(self):
        """Test decorator converts asyncio.TimeoutError."""

        @mcp_error_handler
        async def times_out():
            raise asyncio.TimeoutError()

        with pytest.raises(MCPTimeoutError):
            await times_out()

    @pytest.mark.asyncio
    async def test_error_handler_connection_error_conversion(self):
        """Test decorator converts ConnectionError."""

        @mcp_error_handler
        async def connection_fails():
            raise ConnectionError("Connection refused")

        with pytest.raises(MCPServiceUnavailable):
            await connection_fails()

    @pytest.mark.asyncio
    async def test_error_handler_generic_exception(self):
        """Test decorator handles generic exceptions."""

        @mcp_error_handler
        async def raises_generic_error():
            raise RuntimeError("Something went wrong")

        with pytest.raises(MCPToolError) as exc_info:
            await raises_generic_error()

        error = exc_info.value
        assert error.error_code == MCPErrorCode.INTERNAL_ERROR
        assert "unexpected error" in error.message.lower()

    @pytest.mark.asyncio
    async def test_error_handler_with_retry(self):
        """Test decorator with retry configuration."""
        call_count = 0

        @mcp_error_handler(
            retry_config=RetryConfig(max_attempts=3, base_delay=0.01)
        )
        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise MCPServiceUnavailable("Temporary failure")
            return "success"

        result = await eventually_succeeds()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_error_handler_with_circuit_breaker(self):
        """Test decorator with circuit breaker."""

        @mcp_error_handler(
            circuit_breaker_name="test_cb",
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=2),
        )
        async def may_fail():
            raise MCPServiceUnavailable("Service down")

        # First two failures
        for i in range(2):
            with pytest.raises(MCPServiceUnavailable):
                await may_fail()

        # Third attempt should be rejected by circuit breaker
        with pytest.raises(MCPCircuitOpenError):
            await may_fail()


# ============================================================================
# Metrics Tests
# ============================================================================


class TestErrorMetrics:
    """Test error metrics tracking."""

    def setup_method(self):
        """Reset metrics before each test."""
        reset_error_metrics()

    def test_record_error(self):
        """Test recording errors."""
        record_error(MCPErrorCode.VALIDATION_ERROR, "validate_schedule")
        record_error(MCPErrorCode.VALIDATION_ERROR, "validate_schedule")
        record_error(MCPErrorCode.TIMEOUT, "analyze_swap")

        metrics = get_error_metrics()

        assert metrics["total_errors"] == 3
        assert metrics["errors_by_code"]["VALIDATION_ERROR"] == 2
        assert metrics["errors_by_code"]["TIMEOUT"] == 1
        assert metrics["errors_by_tool"]["validate_schedule"] == 2
        assert metrics["errors_by_tool"]["analyze_swap"] == 1

    def test_reset_metrics(self):
        """Test resetting metrics."""
        record_error(MCPErrorCode.INTERNAL_ERROR)

        reset_error_metrics()
        metrics = get_error_metrics()

        assert metrics["total_errors"] == 0
        assert len(metrics["errors_by_code"]) == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests combining multiple features."""

    @pytest.mark.asyncio
    async def test_full_error_handling_stack(self):
        """Test complete error handling with retry and circuit breaker."""
        attempt_count = 0

        @mcp_error_handler(
            retry_config=RetryConfig(max_attempts=3, base_delay=0.01),
            circuit_breaker_name="integration_test",
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5),
        )
        async def complex_operation(should_succeed: bool):
            nonlocal attempt_count
            attempt_count += 1

            if not should_succeed:
                raise MCPServiceUnavailable("Service temporarily down")

            return {"status": "completed", "attempts": attempt_count}

        # Test successful retry
        attempt_count = 0
        # First two calls fail, third succeeds
        with pytest.raises(MCPServiceUnavailable):
            await complex_operation(should_succeed=False)

        # Verify circuit breaker state is tracked
        cb_states = get_all_circuit_breakers()
        assert "integration_test" in cb_states

    @pytest.mark.asyncio
    async def test_error_response_structure(self):
        """Test that error responses have correct structure."""

        @mcp_error_handler
        async def failing_tool():
            raise MCPValidationError(
                message="Invalid date range",
                field="end_date",
                details={"reason": "end_date before start_date"},
            )

        try:
            await failing_tool()
        except MCPValidationError as e:
            error_dict = e.to_dict()

            # Verify structure
            assert error_dict["error"] is True
            assert error_dict["error_code"] == "VALIDATION_ERROR"
            assert error_dict["message"] == "Invalid date range"
            assert "correlation_id" in error_dict
            assert "timestamp" in error_dict
            assert error_dict["details"]["field"] == "end_date"
            assert error_dict["details"]["reason"] == "end_date before start_date"
