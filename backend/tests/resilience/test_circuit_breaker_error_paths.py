"""Tests for circuit breaker error paths and state transitions.

Covers:
- CircuitBreaker.call() sync error paths
- CircuitBreaker.call_async() async error paths
- CircuitOpenError when circuit is open
- Fallback function invocation (success and failure)
- Excluded exceptions bypass failure counting
- State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
- Manual force_open / force_close
- Reset to initial state
- Half-open call limiting
- Context manager error handling
"""

import asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock

import pytest

from app.resilience.circuit_breaker.breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerTimeoutError,
    CircuitOpenError,
)
from app.resilience.circuit_breaker.states import CircuitState, StateMachine


# ---------------------------------------------------------------------------
# StateMachine tests
# ---------------------------------------------------------------------------


class TestStateMachine:
    """Tests for the circuit breaker StateMachine."""

    def test_initial_state_is_closed(self):
        """State machine starts in CLOSED state."""
        sm = StateMachine()
        assert sm.current_state == CircuitState.CLOSED

    def test_failures_below_threshold_stay_closed(self):
        """Failures below threshold keep circuit CLOSED."""
        sm = StateMachine(failure_threshold=3)
        sm.record_failure()
        sm.record_failure()
        assert sm.current_state == CircuitState.CLOSED

    def test_failures_at_threshold_opens_circuit(self):
        """Reaching failure threshold transitions to OPEN."""
        sm = StateMachine(failure_threshold=3)
        for _ in range(3):
            sm.record_failure()
        assert sm.current_state == CircuitState.OPEN

    def test_success_resets_consecutive_failures(self):
        """A success resets the consecutive failure counter."""
        sm = StateMachine(failure_threshold=3)
        sm.record_failure()
        sm.record_failure()
        sm.record_success()
        # After success, consecutive failures reset so another 2 failures
        # should not trip the breaker
        sm.record_failure()
        sm.record_failure()
        assert sm.current_state == CircuitState.CLOSED

    def test_open_rejects_requests(self):
        """Open circuit rejects new requests."""
        sm = StateMachine(failure_threshold=1, timeout_seconds=3600)
        sm.record_failure()
        assert sm.current_state == CircuitState.OPEN
        assert sm.should_allow_request() is False

    def test_open_transitions_to_half_open_after_timeout(self):
        """After timeout, OPEN transitions to HALF_OPEN on request check."""
        sm = StateMachine(failure_threshold=1, timeout_seconds=0.001)
        sm.record_failure()
        assert sm.current_state == CircuitState.OPEN

        # Simulate timeout passing
        sm.opened_at = datetime.now(UTC) - timedelta(seconds=1)
        assert sm.should_allow_request() is True
        assert sm.current_state == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self):
        """Enough successes in HALF_OPEN transitions to CLOSED."""
        sm = StateMachine(
            failure_threshold=1, success_threshold=2, timeout_seconds=0.001
        )
        sm.record_failure()
        sm.opened_at = datetime.now(UTC) - timedelta(seconds=1)
        sm.should_allow_request()  # Transitions to HALF_OPEN

        sm.record_success()
        assert sm.current_state == CircuitState.HALF_OPEN
        sm.record_success()
        assert sm.current_state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        """Any failure in HALF_OPEN transitions back to OPEN."""
        sm = StateMachine(failure_threshold=1, timeout_seconds=0.001)
        sm.record_failure()
        sm.opened_at = datetime.now(UTC) - timedelta(seconds=1)
        sm.should_allow_request()  # Transitions to HALF_OPEN

        sm.record_failure()
        assert sm.current_state == CircuitState.OPEN

    def test_half_open_limits_concurrent_calls(self):
        """HALF_OPEN limits concurrent calls to half_open_max_calls."""
        sm = StateMachine(
            failure_threshold=1,
            timeout_seconds=0.001,
            half_open_max_calls=2,
        )
        sm.record_failure()
        sm.opened_at = datetime.now(UTC) - timedelta(seconds=1)
        sm.should_allow_request()  # Transitions to HALF_OPEN

        sm.half_open_calls_in_flight = 2
        assert sm.should_allow_request() is False

    def test_force_open(self):
        """force_open transitions from CLOSED to OPEN."""
        sm = StateMachine()
        sm.force_open("Manual override")
        assert sm.current_state == CircuitState.OPEN

    def test_force_open_when_already_open(self):
        """force_open is idempotent when already OPEN."""
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        transitions_before = len(sm.metrics.state_transitions)
        sm.force_open("Already open")
        # Should not add another transition
        assert len(sm.metrics.state_transitions) == transitions_before

    def test_force_closed(self):
        """force_closed transitions from OPEN to CLOSED."""
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        sm.force_closed("Manual override")
        assert sm.current_state == CircuitState.CLOSED

    def test_reset_clears_all_state(self):
        """reset clears metrics and returns to initial state."""
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        sm.reset()
        assert sm.current_state == CircuitState.CLOSED
        assert sm.metrics.total_requests == 0
        assert sm.metrics.failed_requests == 0
        assert sm.opened_at is None

    def test_rejection_tracking(self):
        """Rejected requests are counted separately."""
        sm = StateMachine(failure_threshold=1, timeout_seconds=3600)
        sm.record_failure()  # Open circuit
        sm.record_rejection()
        sm.record_rejection()
        assert sm.metrics.rejected_requests == 2

    def test_get_status_returns_dict(self):
        """get_status returns a complete status dictionary."""
        sm = StateMachine()
        sm.record_success()
        status = sm.get_status()
        assert status["state"] == "closed"
        assert status["total_requests"] == 1
        assert status["successful_requests"] == 1
        assert "failure_rate" in status
        assert "success_rate" in status

    def test_metrics_failure_rate(self):
        """Failure rate is calculated correctly."""
        sm = StateMachine(failure_threshold=10)
        sm.record_success()
        sm.record_success()
        sm.record_failure()
        assert sm.metrics.failure_rate == pytest.approx(1 / 3)

    def test_metrics_success_rate(self):
        """Success rate is calculated correctly."""
        sm = StateMachine(failure_threshold=10)
        sm.record_success()
        sm.record_success()
        sm.record_failure()
        assert sm.metrics.success_rate == pytest.approx(2 / 3)

    def test_metrics_zero_requests(self):
        """Zero requests returns 0 for both rates."""
        sm = StateMachine()
        assert sm.metrics.failure_rate == 0.0
        assert sm.metrics.success_rate == 0.0


# ---------------------------------------------------------------------------
# CircuitBreaker.call() sync tests
# ---------------------------------------------------------------------------


class TestCircuitBreakerSyncCall:
    """Tests for CircuitBreaker.call() synchronous path."""

    def test_successful_call(self):
        """Successful function call passes through."""
        config = CircuitBreakerConfig(name="test", failure_threshold=3)
        cb = CircuitBreaker(config)

        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.state == CircuitState.CLOSED

    def test_failure_increments_count(self):
        """Failed function call increments failure counter."""
        config = CircuitBreakerConfig(name="test", failure_threshold=3)
        cb = CircuitBreaker(config)

        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

    def test_circuit_opens_after_threshold(self):
        """Circuit opens after reaching failure threshold."""
        config = CircuitBreakerConfig(name="test", failure_threshold=2)
        cb = CircuitBreaker(config)

        def failing():
            raise ConnectionError("fail")

        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(failing)

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_raises_circuit_open_error(self):
        """Open circuit raises CircuitOpenError immediately."""
        config = CircuitBreakerConfig(
            name="test", failure_threshold=1, timeout_seconds=3600
        )
        cb = CircuitBreaker(config)

        with pytest.raises(ConnectionError):
            cb.call(lambda: (_ for _ in ()).throw(ConnectionError()))

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 42)

    def test_fallback_on_open_circuit(self):
        """Fallback function is called when circuit is open."""
        config = CircuitBreakerConfig(
            name="test",
            failure_threshold=1,
            timeout_seconds=3600,
            fallback_function=lambda: "fallback",
        )
        cb = CircuitBreaker(config)

        # The first call fails, but fallback catches the error
        result = cb.call(lambda: (_ for _ in ()).throw(ConnectionError()))
        assert result == "fallback"
        assert cb.state == CircuitState.OPEN

        # Subsequent calls also use fallback (circuit is open)
        result = cb.call(lambda: 42)
        assert result == "fallback"

    def test_fallback_on_failure(self):
        """Fallback function is called when the call fails (not just open)."""
        config = CircuitBreakerConfig(
            name="test",
            failure_threshold=10,
            fallback_function=lambda: "fallback_value",
        )
        cb = CircuitBreaker(config)

        result = cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        assert result == "fallback_value"

    def test_excluded_exception_not_counted(self):
        """Excluded exceptions are re-raised but not counted as failures."""
        config = CircuitBreakerConfig(
            name="test",
            failure_threshold=1,
            excluded_exceptions=(ValueError,),
        )
        cb = CircuitBreaker(config)

        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("expected")))

        # Circuit should still be CLOSED because ValueError is excluded
        assert cb.state == CircuitState.CLOSED

    def test_get_status(self):
        """get_status returns a properly structured dict."""
        config = CircuitBreakerConfig(name="test_breaker")
        cb = CircuitBreaker(config)
        status = cb.get_status()
        assert status["name"] == "test_breaker"
        assert status["state"] == "closed"


# ---------------------------------------------------------------------------
# CircuitBreaker.call_async() async tests
# ---------------------------------------------------------------------------


class TestCircuitBreakerAsyncCall:
    """Tests for CircuitBreaker.call_async() asynchronous path."""

    @pytest.mark.asyncio
    async def test_successful_async_call(self):
        """Successful async call passes through."""
        config = CircuitBreakerConfig(name="test_async")
        cb = CircuitBreaker(config)

        async def success():
            return "ok"

        result = await cb.call_async(success)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_async_failure_opens_circuit(self):
        """Async failures open the circuit."""
        config = CircuitBreakerConfig(name="test_async", failure_threshold=2)
        cb = CircuitBreaker(config)

        async def failing():
            raise OSError("fail")

        for _ in range(2):
            with pytest.raises(IOError):
                await cb.call_async(failing)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_async_open_circuit_raises(self):
        """Open circuit raises CircuitOpenError for async calls."""
        config = CircuitBreakerConfig(
            name="test_async", failure_threshold=1, timeout_seconds=3600
        )
        cb = CircuitBreaker(config)

        async def failing():
            raise OSError("fail")

        with pytest.raises(IOError):
            await cb.call_async(failing)

        with pytest.raises(CircuitOpenError):
            await cb.call_async(failing)

    @pytest.mark.asyncio
    async def test_async_fallback_on_open(self):
        """Async fallback function is used when circuit is open."""

        async def async_fallback():
            return "async_fallback"

        config = CircuitBreakerConfig(
            name="test_async",
            failure_threshold=1,
            timeout_seconds=3600,
            fallback_function=async_fallback,
        )
        cb = CircuitBreaker(config)

        async def failing():
            raise OSError("fail")

        # First call fails but fallback catches it
        result = await cb.call_async(failing)
        assert result == "async_fallback"
        assert cb.state == CircuitState.OPEN

        # Subsequent calls also use fallback (circuit open)
        result = await cb.call_async(failing)
        assert result == "async_fallback"

    @pytest.mark.asyncio
    async def test_async_sync_fallback_on_open(self):
        """Sync fallback function works for async calls when circuit is open."""
        config = CircuitBreakerConfig(
            name="test_async",
            failure_threshold=1,
            timeout_seconds=3600,
            fallback_function=lambda: "sync_fallback",
        )
        cb = CircuitBreaker(config)

        async def failing():
            raise OSError("fail")

        # First call fails but fallback catches it
        result = await cb.call_async(failing)
        assert result == "sync_fallback"
        assert cb.state == CircuitState.OPEN

        # Subsequent calls also use fallback (circuit open)
        result = await cb.call_async(failing)
        assert result == "sync_fallback"

    @pytest.mark.asyncio
    async def test_async_timeout(self):
        """Call timeout raises CircuitBreakerTimeoutError for async."""
        config = CircuitBreakerConfig(
            name="test_async",
            call_timeout_seconds=0.01,
        )
        cb = CircuitBreaker(config)

        async def slow():
            await asyncio.sleep(10)
            return "slow"

        with pytest.raises(CircuitBreakerTimeoutError):
            await cb.call_async(slow)

    @pytest.mark.asyncio
    async def test_async_excluded_exception(self):
        """Excluded exceptions in async path are not counted."""
        config = CircuitBreakerConfig(
            name="test_async",
            failure_threshold=1,
            excluded_exceptions=(KeyError,),
        )
        cb = CircuitBreaker(config)

        async def raises_key_error():
            raise KeyError("expected")

        with pytest.raises(KeyError):
            await cb.call_async(raises_key_error)

        assert cb.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# Context manager tests
# ---------------------------------------------------------------------------


class TestCircuitBreakerContextManager:
    """Tests for CircuitBreaker as context manager."""

    def test_sync_context_manager_success(self):
        """Sync context manager records success."""
        config = CircuitBreakerConfig(name="ctx_test")
        cb = CircuitBreaker(config)

        with cb():
            pass  # Success

        assert cb.state_machine.metrics.successful_requests == 1

    def test_sync_context_manager_failure(self):
        """Sync context manager records failure on exception."""
        config = CircuitBreakerConfig(name="ctx_test", failure_threshold=1)
        cb = CircuitBreaker(config)

        with pytest.raises(RuntimeError):
            with cb():
                raise RuntimeError("fail")

        assert cb.state == CircuitState.OPEN

    def test_sync_context_manager_open_raises(self):
        """Open circuit raises immediately from context manager."""
        config = CircuitBreakerConfig(
            name="ctx_test", failure_threshold=1, timeout_seconds=3600
        )
        cb = CircuitBreaker(config)
        cb.open("test")

        with pytest.raises(CircuitOpenError):
            with cb():
                pass

    @pytest.mark.asyncio
    async def test_async_context_manager_success(self):
        """Async context manager records success."""
        config = CircuitBreakerConfig(name="async_ctx_test")
        cb = CircuitBreaker(config)

        async with cb.async_call():
            pass

        assert cb.state_machine.metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_async_context_manager_failure(self):
        """Async context manager records failure on exception."""
        config = CircuitBreakerConfig(name="async_ctx_test", failure_threshold=1)
        cb = CircuitBreaker(config)

        with pytest.raises(RuntimeError):
            async with cb.async_call():
                raise RuntimeError("fail")

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_async_context_manager_open_raises(self):
        """Open circuit raises immediately from async context manager."""
        config = CircuitBreakerConfig(
            name="async_ctx_test", failure_threshold=1, timeout_seconds=3600
        )
        cb = CircuitBreaker(config)
        cb.open("test")

        with pytest.raises(CircuitOpenError):
            async with cb.async_call():
                pass


# ---------------------------------------------------------------------------
# Manual control
# ---------------------------------------------------------------------------


class TestCircuitBreakerManualControl:
    """Tests for manual circuit breaker control."""

    def test_manual_open_and_close(self):
        """Can manually open and close the circuit."""
        config = CircuitBreakerConfig(name="manual_test")
        cb = CircuitBreaker(config)

        assert cb.state == CircuitState.CLOSED
        cb.open("Testing")
        assert cb.state == CircuitState.OPEN
        cb.close("Done testing")
        assert cb.state == CircuitState.CLOSED

    def test_reset_clears_everything(self):
        """Reset returns circuit to fresh initial state."""
        config = CircuitBreakerConfig(name="reset_test", failure_threshold=1)
        cb = CircuitBreaker(config)

        # Trip the breaker
        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))

        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.state_machine.metrics.total_requests == 0
