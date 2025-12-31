"""Tests for Circuit Breaker Implementation.

Comprehensive unit tests for the circuit breaker pattern implementation,
including state machine, breaker logic, registry, decorators, and monitoring.
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from app.resilience.circuit_breaker.breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerTimeoutError,
    CircuitOpenError,
)
from app.resilience.circuit_breaker.decorators import (
    async_circuit_breaker,
    circuit_breaker,
    get_breaker_from_function,
    get_breaker_name_from_function,
    with_async_circuit_breaker,
    with_circuit_breaker,
)
from app.resilience.circuit_breaker.registry import (
    CircuitBreakerRegistry,
    get_registry,
    setup_registry,
)
from app.resilience.circuit_breaker.states import (
    CircuitMetrics,
    CircuitState,
    StateTransition,
    StateMachine,
)


# ============================================================================
# StateMachine Tests
# ============================================================================


class TestStateMachine:
    """Test suite for circuit breaker state machine."""

    @pytest.fixture
    def state_machine(self):
        """Create a state machine with default settings."""
        return StateMachine(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0,
            half_open_max_calls=2,
        )

    def test_initialization(self, state_machine):
        """Test state machine initializes in CLOSED state."""
        assert state_machine.current_state == CircuitState.CLOSED
        assert state_machine.failure_threshold == 3
        assert state_machine.success_threshold == 2
        assert state_machine.timeout == timedelta(seconds=1.0)
        assert state_machine.half_open_max_calls == 2
        assert state_machine.metrics.total_requests == 0
        assert state_machine.opened_at is None

    def test_record_success_in_closed_state(self, state_machine):
        """Test recording success in CLOSED state."""
        state = state_machine.record_success()

        assert state == CircuitState.CLOSED
        assert state_machine.metrics.total_requests == 1
        assert state_machine.metrics.successful_requests == 1
        assert state_machine.metrics.consecutive_successes == 1
        assert state_machine.metrics.consecutive_failures == 0
        assert state_machine.metrics.last_success_time is not None

    def test_record_failure_in_closed_state(self, state_machine):
        """Test recording failure in CLOSED state."""
        state = state_machine.record_failure()

        assert state == CircuitState.CLOSED
        assert state_machine.metrics.total_requests == 1
        assert state_machine.metrics.failed_requests == 1
        assert state_machine.metrics.consecutive_failures == 1
        assert state_machine.metrics.consecutive_successes == 0
        assert state_machine.metrics.last_failure_time is not None

    def test_transition_to_open_on_failure_threshold(self, state_machine):
        """Test circuit opens when failure threshold is reached."""
        # Record failures up to threshold
        for _ in range(3):
            state = state_machine.record_failure()

        assert state == CircuitState.OPEN
        assert state_machine.current_state == CircuitState.OPEN
        assert state_machine.opened_at is not None
        assert state_machine.metrics.consecutive_failures == 3

    def test_should_allow_request_in_closed_state(self, state_machine):
        """Test requests are allowed in CLOSED state."""
        assert state_machine.should_allow_request() is True

    def test_should_reject_request_in_open_state(self, state_machine):
        """Test requests are rejected in OPEN state."""
        # Force to OPEN state
        state_machine._transition_to_open("Test")

        assert state_machine.should_allow_request() is False

    def test_transition_to_half_open_after_timeout(self, state_machine):
        """Test circuit transitions to HALF_OPEN after timeout."""
        # Force to OPEN state
        state_machine._transition_to_open("Test")
        assert state_machine.current_state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Check if request should be allowed (triggers transition)
        allowed = state_machine.should_allow_request()

        assert allowed is True
        assert state_machine.current_state == CircuitState.HALF_OPEN

    def test_half_open_limits_concurrent_calls(self, state_machine):
        """Test HALF_OPEN state limits concurrent calls."""
        # Transition to HALF_OPEN
        state_machine._transition_to_half_open("Test")

        # Simulate in-flight calls
        state_machine.half_open_calls_in_flight = 0
        assert state_machine.should_allow_request() is True

        state_machine.half_open_calls_in_flight = 1
        assert state_machine.should_allow_request() is True

        state_machine.half_open_calls_in_flight = 2
        assert state_machine.should_allow_request() is False

    def test_transition_to_closed_on_success_threshold_in_half_open(
        self, state_machine
    ):
        """Test circuit closes when success threshold met in HALF_OPEN."""
        # Transition to HALF_OPEN
        state_machine._transition_to_half_open("Test")

        # Record successes up to threshold
        for _ in range(2):
            state = state_machine.record_success()

        assert state == CircuitState.CLOSED
        assert state_machine.current_state == CircuitState.CLOSED
        assert state_machine.opened_at is None

    def test_transition_to_open_on_failure_in_half_open(self, state_machine):
        """Test circuit returns to OPEN on any failure in HALF_OPEN."""
        # Transition to HALF_OPEN
        state_machine._transition_to_half_open("Test")

        # Record one success, then one failure
        state_machine.record_success()
        state = state_machine.record_failure()

        assert state == CircuitState.OPEN
        assert state_machine.current_state == CircuitState.OPEN

    def test_record_rejection(self, state_machine):
        """Test recording rejected requests."""
        state_machine.record_rejection()
        state_machine.record_rejection()

        assert state_machine.metrics.rejected_requests == 2

    def test_force_open(self, state_machine):
        """Test manually forcing circuit to OPEN."""
        assert state_machine.current_state == CircuitState.CLOSED

        state_machine.force_open("Manual test")

        assert state_machine.current_state == CircuitState.OPEN
        assert state_machine.opened_at is not None

    def test_force_closed(self, state_machine):
        """Test manually forcing circuit to CLOSED."""
        # First open it
        state_machine.force_open("Test")
        assert state_machine.current_state == CircuitState.OPEN

        # Then force close
        state_machine.force_closed("Manual test")

        assert state_machine.current_state == CircuitState.CLOSED
        assert state_machine.opened_at is None

    def test_reset(self, state_machine):
        """Test resetting state machine to initial state."""
        # Make some changes
        state_machine.record_failure()
        state_machine.record_failure()
        state_machine._transition_to_open("Test")

        # Reset
        state_machine.reset()

        assert state_machine.current_state == CircuitState.CLOSED
        assert state_machine.metrics.total_requests == 0
        assert state_machine.metrics.failed_requests == 0
        assert state_machine.opened_at is None

    def test_get_status(self, state_machine):
        """Test getting status dictionary."""
        # Record some activity
        state_machine.record_success()
        state_machine.record_failure()

        status = state_machine.get_status()

        assert status["state"] == "closed"
        assert status["total_requests"] == 2
        assert status["successful_requests"] == 1
        assert status["failed_requests"] == 1
        assert status["failure_rate"] == 0.5
        assert status["success_rate"] == 0.5
        assert "last_success_time" in status
        assert "last_failure_time" in status
        assert "recent_transitions" in status

    def test_state_transitions_are_recorded(self, state_machine):
        """Test that state transitions are recorded in metrics."""
        # Trigger a transition
        state_machine._transition_to_open("Test reason")

        assert len(state_machine.metrics.state_transitions) == 1
        transition = state_machine.metrics.state_transitions[0]
        assert isinstance(transition, StateTransition)
        assert transition.from_state == CircuitState.CLOSED
        assert transition.to_state == CircuitState.OPEN
        assert transition.reason == "Test reason"


class TestCircuitMetrics:
    """Test suite for circuit metrics."""

    @pytest.fixture
    def metrics(self):
        """Create a CircuitMetrics instance."""
        return CircuitMetrics()

    def test_initialization(self, metrics):
        """Test metrics initialize with zeros."""
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.rejected_requests == 0
        assert metrics.consecutive_failures == 0
        assert metrics.consecutive_successes == 0
        assert metrics.last_failure_time is None
        assert metrics.last_success_time is None

    def test_failure_rate_calculation(self, metrics):
        """Test failure rate calculation."""
        # No requests yet
        assert metrics.failure_rate == 0.0

        # Add some requests
        metrics.total_requests = 10
        metrics.failed_requests = 3

        assert metrics.failure_rate == 0.3

    def test_success_rate_calculation(self, metrics):
        """Test success rate calculation."""
        # No requests yet
        assert metrics.success_rate == 0.0

        # Add some requests
        metrics.total_requests = 10
        metrics.successful_requests = 7

        assert metrics.success_rate == 0.7

    def test_reset_consecutive_counters(self, metrics):
        """Test resetting consecutive counters."""
        metrics.consecutive_failures = 5
        metrics.consecutive_successes = 3

        metrics.reset_consecutive_counters()

        assert metrics.consecutive_failures == 0
        assert metrics.consecutive_successes == 0


# ============================================================================
# CircuitBreaker Tests
# ============================================================================


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    @pytest.fixture
    def breaker_config(self):
        """Create a circuit breaker configuration."""
        return CircuitBreakerConfig(
            name="test_breaker",
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0,
            half_open_max_calls=2,
        )

    @pytest.fixture
    def breaker(self, breaker_config):
        """Create a circuit breaker instance."""
        return CircuitBreaker(breaker_config)

    def test_initialization(self, breaker):
        """Test circuit breaker initializes correctly."""
        assert breaker.name == "test_breaker"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.config is not None
        assert breaker.state_machine is not None

    def test_successful_call(self, breaker):
        """Test successful function call through breaker."""

        def successful_func():
            return "success"

        result = breaker.call(successful_func)

        assert result == "success"
        assert breaker.state_machine.metrics.successful_requests == 1
        assert breaker.state == CircuitState.CLOSED

    def test_failed_call(self, breaker):
        """Test failed function call through breaker."""

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            breaker.call(failing_func)

        assert breaker.state_machine.metrics.failed_requests == 1

    def test_circuit_opens_after_failures(self, breaker):
        """Test circuit opens after failure threshold."""

        def failing_func():
            raise ValueError("Test error")

        # Make calls up to threshold
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

    def test_circuit_rejects_when_open(self, breaker):
        """Test circuit rejects calls when OPEN."""
        # Force circuit open
        breaker.state_machine.force_open("Test")

        def some_func():
            return "should not be called"

        with pytest.raises(CircuitOpenError, match="Circuit breaker .* is OPEN"):
            breaker.call(some_func)

    def test_fallback_function_on_open_circuit(self):
        """Test fallback function is called when circuit is open."""

        def fallback():
            return "fallback_result"

        config = CircuitBreakerConfig(
            name="test_fallback",
            failure_threshold=2,
            fallback_function=fallback,
        )
        breaker = CircuitBreaker(config)

        # Open the circuit
        breaker.state_machine.force_open("Test")

        def main_func():
            return "main_result"

        result = breaker.call(main_func)

        assert result == "fallback_result"

    def test_excluded_exceptions_not_counted(self):
        """Test that excluded exceptions don't count as failures."""

        class SpecialError(Exception):
            pass

        config = CircuitBreakerConfig(
            name="test_excluded",
            failure_threshold=2,
            excluded_exceptions=(SpecialError,),
        )
        breaker = CircuitBreaker(config)

        def raises_special():
            raise SpecialError("Special error")

        # This should raise but not count as failure
        with pytest.raises(SpecialError):
            breaker.call(raises_special)

        assert breaker.state_machine.metrics.failed_requests == 0
        assert breaker.state == CircuitState.CLOSED

    def test_call_with_arguments(self, breaker):
        """Test calling function with arguments."""

        def add(a, b):
            return a + b

        result = breaker.call(add, 5, 3)
        assert result == 8

        result = breaker.call(add, a=10, b=20)
        assert result == 30

    def test_context_manager(self, breaker):
        """Test using breaker as context manager."""
        executed = False

        with breaker():
            executed = True

        assert executed
        assert breaker.state_machine.metrics.successful_requests == 1

    def test_context_manager_with_exception(self, breaker):
        """Test context manager handles exceptions."""
        with pytest.raises(ValueError):
            with breaker():
                raise ValueError("Test error")

        assert breaker.state_machine.metrics.failed_requests == 1

    def test_manual_open(self, breaker):
        """Test manually opening circuit."""
        assert breaker.state == CircuitState.CLOSED

        breaker.open("Manual test")

        assert breaker.state == CircuitState.OPEN

    def test_manual_close(self, breaker):
        """Test manually closing circuit."""
        breaker.open("Test")
        assert breaker.state == CircuitState.OPEN

        breaker.close("Manual test")

        assert breaker.state == CircuitState.CLOSED

    def test_reset(self, breaker):
        """Test resetting circuit breaker."""
        # Generate some activity
        breaker.state_machine.record_failure()
        breaker.open("Test")

        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.state_machine.metrics.total_requests == 0

    def test_get_status(self, breaker):
        """Test getting status dictionary."""
        status = breaker.get_status()

        assert "name" in status
        assert status["name"] == "test_breaker"
        assert "state" in status
        assert "total_requests" in status


class TestCircuitBreakerAsync:
    """Test suite for async circuit breaker functionality."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker for async testing."""
        config = CircuitBreakerConfig(
            name="async_test_breaker",
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0,
        )
        return CircuitBreaker(config)

    @pytest.mark.asyncio
    async def test_successful_async_call(self, breaker):
        """Test successful async function call."""

        async def async_func():
            return "async_success"

        result = await breaker.call_async(async_func)

        assert result == "async_success"
        assert breaker.state_machine.metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_failed_async_call(self, breaker):
        """Test failed async function call."""

        async def failing_async():
            raise ValueError("Async error")

        with pytest.raises(ValueError, match="Async error"):
            await breaker.call_async(failing_async)

        assert breaker.state_machine.metrics.failed_requests == 1

    @pytest.mark.asyncio
    async def test_async_circuit_opens_after_failures(self, breaker):
        """Test async circuit opens after failures."""

        async def failing_async():
            raise ValueError("Async error")

        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call_async(failing_async)

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_async_circuit_rejects_when_open(self, breaker):
        """Test async circuit rejects when OPEN."""
        breaker.state_machine.force_open("Test")

        async def some_async():
            return "should not be called"

        with pytest.raises(CircuitOpenError):
            await breaker.call_async(some_async)

    @pytest.mark.asyncio
    async def test_async_fallback(self):
        """Test async fallback function."""

        async def async_fallback():
            return "async_fallback"

        config = CircuitBreakerConfig(
            name="async_fallback_test",
            failure_threshold=1,
            fallback_function=async_fallback,
        )
        breaker = CircuitBreaker(config)
        breaker.state_machine.force_open("Test")

        async def main_async():
            return "main"

        result = await breaker.call_async(main_async)
        assert result == "async_fallback"

    @pytest.mark.asyncio
    async def test_async_context_manager(self, breaker):
        """Test async context manager."""
        executed = False

        async with breaker.async_call():
            executed = True

        assert executed
        assert breaker.state_machine.metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_async_context_manager_with_exception(self, breaker):
        """Test async context manager handles exceptions."""
        with pytest.raises(ValueError):
            async with breaker.async_call():
                raise ValueError("Async error")

        assert breaker.state_machine.metrics.failed_requests == 1

    @pytest.mark.asyncio
    async def test_async_call_timeout(self):
        """Test async call timeout."""
        config = CircuitBreakerConfig(
            name="timeout_test",
            call_timeout_seconds=0.1,
        )
        breaker = CircuitBreaker(config)

        async def slow_func():
            await asyncio.sleep(1)
            return "slow"

        with pytest.raises(CircuitBreakerTimeoutError):
            await breaker.call_async(slow_func)

    @pytest.mark.asyncio
    async def test_async_with_arguments(self, breaker):
        """Test async call with arguments."""

        async def async_add(a, b):
            return a + b

        result = await breaker.call_async(async_add, 5, 3)
        assert result == 8


# ============================================================================
# Registry Tests
# ============================================================================


class TestCircuitBreakerRegistry:
    """Test suite for CircuitBreakerRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return CircuitBreakerRegistry()

    def test_initialization(self, registry):
        """Test registry initializes correctly."""
        assert registry is not None
        assert len(registry.list_breakers()) == 0

    def test_register_breaker(self, registry):
        """Test registering a circuit breaker."""
        breaker = registry.register(
            "test_service",
            failure_threshold=5,
            timeout_seconds=30,
        )

        assert breaker is not None
        assert breaker.name == "test_service"
        assert "test_service" in registry.list_breakers()

    def test_register_duplicate_raises_error(self, registry):
        """Test registering duplicate breaker raises error."""
        registry.register("test_service")

        with pytest.raises(ValueError, match="already registered"):
            registry.register("test_service")

    def test_get_breaker(self, registry):
        """Test getting a registered breaker."""
        registry.register("test_service")

        breaker = registry.get("test_service")

        assert breaker is not None
        assert breaker.name == "test_service"

    def test_get_nonexistent_breaker_raises_error(self, registry):
        """Test getting non-existent breaker raises error."""
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    def test_get_or_create_existing(self, registry):
        """Test get_or_create with existing breaker."""
        original = registry.register("test_service")

        breaker = registry.get_or_create("test_service")

        assert breaker is original

    def test_get_or_create_new(self, registry):
        """Test get_or_create creates new breaker."""
        breaker = registry.get_or_create("new_service", failure_threshold=10)

        assert breaker is not None
        assert breaker.name == "new_service"
        assert "new_service" in registry.list_breakers()

    def test_exists(self, registry):
        """Test checking if breaker exists."""
        assert registry.exists("test_service") is False

        registry.register("test_service")

        assert registry.exists("test_service") is True

    def test_unregister(self, registry):
        """Test unregistering a breaker."""
        registry.register("test_service")
        assert registry.exists("test_service") is True

        registry.unregister("test_service")

        assert registry.exists("test_service") is False

    def test_unregister_nonexistent_raises_error(self, registry):
        """Test unregistering non-existent breaker raises error."""
        with pytest.raises(KeyError, match="not found"):
            registry.unregister("nonexistent")

    def test_list_breakers(self, registry):
        """Test listing all breakers."""
        registry.register("service1")
        registry.register("service2")
        registry.register("service3")

        breakers = registry.list_breakers()

        assert len(breakers) == 3
        assert "service1" in breakers
        assert "service2" in breakers
        assert "service3" in breakers

    def test_get_all_statuses(self, registry):
        """Test getting all breaker statuses."""
        registry.register("service1")
        registry.register("service2")

        statuses = registry.get_all_statuses()

        assert len(statuses) == 2
        assert "service1" in statuses
        assert "service2" in statuses
        assert "state" in statuses["service1"]

    def test_reset_all(self, registry):
        """Test resetting all breakers."""
        breaker1 = registry.register("service1")
        breaker2 = registry.register("service2")

        # Generate some activity
        breaker1.state_machine.record_failure()
        breaker2.state_machine.record_failure()

        registry.reset_all()

        assert breaker1.state_machine.metrics.total_requests == 0
        assert breaker2.state_machine.metrics.total_requests == 0

    def test_open_all(self, registry):
        """Test opening all breakers."""
        breaker1 = registry.register("service1")
        breaker2 = registry.register("service2")

        registry.open_all("Test")

        assert breaker1.state == CircuitState.OPEN
        assert breaker2.state == CircuitState.OPEN

    def test_close_all(self, registry):
        """Test closing all breakers."""
        breaker1 = registry.register("service1")
        breaker2 = registry.register("service2")

        # Open them first
        registry.open_all("Test")

        # Then close
        registry.close_all("Test")

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED

    def test_get_open_breakers(self, registry):
        """Test getting list of open breakers."""
        breaker1 = registry.register("service1")
        registry.register("service2")

        breaker1.open("Test")

        open_breakers = registry.get_open_breakers()

        assert len(open_breakers) == 1
        assert "service1" in open_breakers

    def test_get_half_open_breakers(self, registry):
        """Test getting list of half-open breakers."""
        breaker1 = registry.register("service1")
        registry.register("service2")

        breaker1.state_machine._transition_to_half_open("Test")

        half_open_breakers = registry.get_half_open_breakers()

        assert len(half_open_breakers) == 1
        assert "service1" in half_open_breakers

    def test_health_check(self, registry):
        """Test health check returns correct summary."""
        registry.register("service1")
        breaker2 = registry.register("service2")

        breaker2.open("Test")

        health = registry.health_check()

        assert health["total_breakers"] == 2
        assert health["open_breakers"] == 1
        assert health["closed_breakers"] == 1
        assert "service2" in health["open_breaker_names"]

    def test_set_default_config(self, registry):
        """Test setting default configuration."""
        default_config = CircuitBreakerConfig(
            name="default",
            failure_threshold=10,
            timeout_seconds=120,
        )

        registry.set_default_config(default_config)

        # New breakers should use default config
        breaker = registry.register("test_service")

        assert breaker.config.failure_threshold == 10
        assert breaker.config.timeout_seconds == 120

    def test_register_with_full_config(self, registry):
        """Test registering with full config object."""
        config = CircuitBreakerConfig(
            name="custom_service",
            failure_threshold=7,
            success_threshold=3,
            timeout_seconds=45,
        )

        breaker = registry.register("custom_service", config=config)

        assert breaker.config.failure_threshold == 7
        assert breaker.config.success_threshold == 3
        assert breaker.config.timeout_seconds == 45


class TestRegistryGlobalFunctions:
    """Test global registry functions."""

    def test_get_registry_singleton(self):
        """Test get_registry returns singleton."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_setup_registry_creates_new(self):
        """Test setup_registry creates new instance."""
        old_registry = get_registry()

        new_registry = setup_registry()

        assert new_registry is not old_registry
        # After setup, get_registry should return the new one
        assert get_registry() is new_registry


# ============================================================================
# Decorator Tests
# ============================================================================


class TestCircuitBreakerDecorators:
    """Test suite for circuit breaker decorators."""

    def test_circuit_breaker_decorator(self):
        """Test @circuit_breaker decorator."""

        @circuit_breaker(name="test_func", failure_threshold=2)
        def my_function():
            return "success"

        result = my_function()

        assert result == "success"

        # Check that breaker was registered
        registry = get_registry()
        assert registry.exists("test_func")

    def test_circuit_breaker_decorator_default_name(self):
        """Test decorator uses function name by default."""

        @circuit_breaker(failure_threshold=2)
        def my_named_function():
            return "success"

        result = my_named_function()

        assert result == "success"

        registry = get_registry()
        assert registry.exists("my_named_function")

    def test_circuit_breaker_with_fallback(self):
        """Test decorator with fallback function."""

        def fallback_func():
            return "fallback"

        @circuit_breaker(name="test_fallback", failure_threshold=1, fallback=fallback_func)
        def failing_func():
            raise ValueError("Error")

        # First call fails and opens circuit
        with pytest.raises(ValueError):
            failing_func()

        # Second call uses fallback
        result = failing_func()
        assert result == "fallback"

    def test_get_breaker_from_function(self):
        """Test getting breaker from decorated function."""

        @circuit_breaker(name="test_introspect")
        def my_func():
            return "test"

        breaker = get_breaker_from_function(my_func)

        assert breaker is not None
        assert breaker.name == "test_introspect"

    def test_get_breaker_name_from_function(self):
        """Test getting breaker name from decorated function."""

        @circuit_breaker(name="test_name")
        def my_func():
            return "test"

        name = get_breaker_name_from_function(my_func)

        assert name == "test_name"

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_decorator(self):
        """Test @async_circuit_breaker decorator."""

        @async_circuit_breaker(name="async_test_func", failure_threshold=2)
        async def my_async_function():
            return "async_success"

        result = await my_async_function()

        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_async_decorator_raises_on_sync_function(self):
        """Test async decorator raises error on sync function."""
        with pytest.raises(TypeError, match="async functions"):

            @async_circuit_breaker(name="invalid")
            def sync_func():
                return "test"

    def test_with_circuit_breaker_decorator(self):
        """Test @with_circuit_breaker decorator."""
        # First register a breaker
        registry = get_registry()
        registry.register("shared_breaker", failure_threshold=2)

        @with_circuit_breaker("shared_breaker")
        def func1():
            return "func1"

        @with_circuit_breaker("shared_breaker")
        def func2():
            return "func2"

        result1 = func1()
        result2 = func2()

        assert result1 == "func1"
        assert result2 == "func2"

        # Both should use the same breaker
        breaker = registry.get("shared_breaker")
        assert breaker.state_machine.metrics.total_requests == 2

    @pytest.mark.asyncio
    async def test_with_async_circuit_breaker_decorator(self):
        """Test @with_async_circuit_breaker decorator."""
        registry = get_registry()
        registry.register("shared_async_breaker", failure_threshold=2)

        @with_async_circuit_breaker("shared_async_breaker")
        async def async_func():
            return "async_result"

        result = await async_func()

        assert result == "async_result"

    @pytest.mark.asyncio
    async def test_with_async_decorator_raises_on_sync_function(self):
        """Test with_async decorator raises error on sync function."""
        registry = get_registry()
        registry.register("test_breaker")

        with pytest.raises(TypeError, match="async functions"):

            @with_async_circuit_breaker("test_breaker")
            def sync_func():
                return "test"


# ============================================================================
# Integration Tests
# ============================================================================


class TestCircuitBreakerIntegration:
    """Integration tests for complete circuit breaker workflows."""

    def test_full_circuit_lifecycle(self):
        """Test complete circuit lifecycle: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
        config = CircuitBreakerConfig(
            name="lifecycle_test",
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.5,
        )
        breaker = CircuitBreaker(config)

        # Start CLOSED
        assert breaker.state == CircuitState.CLOSED

        # Trigger failures to OPEN
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.6)

        # Next call should transition to HALF_OPEN
        success_func = lambda: "success"
        result = breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success should close circuit
        result = breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_multiple_breakers_independent(self):
        """Test that multiple breakers operate independently."""
        registry = CircuitBreakerRegistry()

        breaker1 = registry.register("service1", failure_threshold=2)
        breaker2 = registry.register("service2", failure_threshold=2)

        # Fail breaker1
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker1.call(lambda: (_ for _ in ()).throw(ValueError("Error")))

        # breaker1 should be OPEN, breaker2 should be CLOSED
        assert breaker1.state == CircuitState.OPEN
        assert breaker2.state == CircuitState.CLOSED

        # breaker2 should still accept calls
        result = breaker2.call(lambda: "success")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_full_lifecycle(self):
        """Test async circuit full lifecycle."""
        config = CircuitBreakerConfig(
            name="async_lifecycle",
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.5,
        )
        breaker = CircuitBreaker(config)

        # Fail to open
        async def failing():
            raise ValueError("Async error")

        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call_async(failing)

        assert breaker.state == CircuitState.OPEN

        # Wait and recover
        await asyncio.sleep(0.6)

        async def success():
            return "async_success"

        result = await breaker.call_async(success)
        assert breaker.state == CircuitState.HALF_OPEN

        result = await breaker.call_async(success)
        assert breaker.state == CircuitState.CLOSED

    def test_fallback_chain(self):
        """Test fallback functions are called correctly."""
        fallback_called = []

        def fallback():
            fallback_called.append(True)
            return "fallback_value"

        config = CircuitBreakerConfig(
            name="fallback_test",
            failure_threshold=1,
            fallback_function=fallback,
        )
        breaker = CircuitBreaker(config)

        # Open circuit
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("Error")))

        # Next call should use fallback
        result = breaker.call(lambda: "main")

        assert result == "fallback_value"
        assert len(fallback_called) == 1
