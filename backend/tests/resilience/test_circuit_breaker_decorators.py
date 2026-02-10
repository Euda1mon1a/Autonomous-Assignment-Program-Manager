"""Tests for circuit breaker decorators (pure logic, no DB)."""

import pytest

from app.resilience.circuit_breaker.decorators import (
    circuit_breaker,
    get_breaker_from_function,
    get_breaker_name_from_function,
    with_circuit_breaker,
)
from app.resilience.circuit_breaker.registry import setup_registry
from app.resilience.circuit_breaker.states import CircuitState


@pytest.fixture(autouse=True)
def fresh_registry():
    """Reset global registry before each test."""
    setup_registry()


# -- @circuit_breaker decorator ----------------------------------------------


class TestCircuitBreakerDecorator:
    def test_wraps_function(self):
        @circuit_breaker(name="test-wrap")
        def my_func():
            return 42

        assert my_func() == 42

    def test_preserves_function_name(self):
        @circuit_breaker(name="name-test")
        def original_name():
            return 1

        assert original_name.__name__ == "original_name"

    def test_passes_args(self):
        @circuit_breaker(name="args-test")
        def add(a, b):
            return a + b

        assert add(3, 4) == 7

    def test_passes_kwargs(self):
        @circuit_breaker(name="kwargs-test")
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}"

        assert greet("World", greeting="Hi") == "Hi, World"

    def test_default_name_from_function(self):
        @circuit_breaker()
        def auto_named_func():
            return True

        name = get_breaker_name_from_function(auto_named_func)
        assert name == "auto_named_func"

    def test_custom_name(self):
        @circuit_breaker(name="custom-cb")
        def some_func():
            return True

        name = get_breaker_name_from_function(some_func)
        assert name == "custom-cb"

    def test_attaches_breaker(self):
        @circuit_breaker(name="attach-test")
        def decorated():
            return True

        breaker = get_breaker_from_function(decorated)
        assert breaker is not None
        assert breaker.name == "attach-test"

    def test_circuit_opens_on_failures(self):
        @circuit_breaker(name="open-test", failure_threshold=2)
        def failing():
            raise RuntimeError("boom")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                failing()

        breaker = get_breaker_from_function(failing)
        assert breaker.state == CircuitState.OPEN

    def test_fallback_used(self):
        @circuit_breaker(
            name="fb-decorator",
            failure_threshold=1,
            fallback=lambda: "cached",
        )
        def risky():
            raise RuntimeError("fail")

        # First call uses fallback on failure
        result = risky()
        assert result == "cached"

    def test_excluded_exceptions(self):
        @circuit_breaker(
            name="excl-decorator",
            excluded_exceptions=(ValueError,),
        )
        def raises_value_error():
            raise ValueError("expected")

        with pytest.raises(ValueError):
            raises_value_error()

        breaker = get_breaker_from_function(raises_value_error)
        assert breaker.state_machine.metrics.failed_requests == 0


# -- @with_circuit_breaker decorator -----------------------------------------


class TestWithCircuitBreaker:
    def test_uses_existing_breaker(self):
        from app.resilience.circuit_breaker.registry import get_registry

        reg = get_registry()
        reg.register("shared-breaker")

        @with_circuit_breaker("shared-breaker")
        def my_func():
            return "ok"

        result = my_func()
        assert result == "ok"

        breaker = reg.get("shared-breaker")
        assert breaker.state_machine.metrics.successful_requests == 1

    def test_attaches_name(self):
        from app.resilience.circuit_breaker.registry import get_registry

        get_registry().register("named-shared")

        @with_circuit_breaker("named-shared")
        def my_func():
            return True

        assert get_breaker_name_from_function(my_func) == "named-shared"

    def test_missing_breaker_raises(self):
        @with_circuit_breaker("nonexistent")
        def func():
            return True

        with pytest.raises(KeyError, match="not found"):
            func()


# -- get_breaker_from_function / get_breaker_name_from_function --------------


class TestIntrospection:
    def test_get_breaker_from_undecorated(self):
        def plain():
            return True

        assert get_breaker_from_function(plain) is None

    def test_get_name_from_undecorated(self):
        def plain():
            return True

        assert get_breaker_name_from_function(plain) is None

    def test_get_breaker_returns_correct_instance(self):
        @circuit_breaker(name="introspect-test")
        def func():
            return True

        breaker = get_breaker_from_function(func)
        assert breaker.name == "introspect-test"
        assert breaker.state == CircuitState.CLOSED
