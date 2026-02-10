"""Tests for circuit breaker (pure logic, no DB)."""

import pytest

from app.resilience.circuit_breaker.breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerTimeoutError,
    CircuitOpenError,
)
from app.resilience.circuit_breaker.states import CircuitState


# -- Exception hierarchy -----------------------------------------------------


class TestExceptionHierarchy:
    def test_circuit_breaker_error_is_exception(self):
        assert issubclass(CircuitBreakerError, Exception)

    def test_circuit_open_error_is_circuit_breaker_error(self):
        assert issubclass(CircuitOpenError, CircuitBreakerError)

    def test_circuit_timeout_error_is_circuit_breaker_error(self):
        assert issubclass(CircuitBreakerTimeoutError, CircuitBreakerError)

    def test_circuit_open_error_message(self):
        err = CircuitOpenError("test message")
        assert str(err) == "test message"

    def test_circuit_timeout_error_message(self):
        err = CircuitBreakerTimeoutError("timed out")
        assert str(err) == "timed out"


# -- CircuitBreakerConfig ---------------------------------------------------


class TestCircuitBreakerConfig:
    def test_defaults(self):
        cfg = CircuitBreakerConfig(name="test")
        assert cfg.name == "test"
        assert cfg.failure_threshold == 5
        assert cfg.success_threshold == 2
        assert cfg.timeout_seconds == 60.0
        assert cfg.call_timeout_seconds is None
        assert cfg.half_open_max_calls == 3
        assert cfg.excluded_exceptions == ()
        assert cfg.fallback_function is None

    def test_custom_values(self):
        def fallback():
            return "fallback"

        cfg = CircuitBreakerConfig(
            name="custom",
            failure_threshold=3,
            success_threshold=1,
            timeout_seconds=30.0,
            call_timeout_seconds=5.0,
            half_open_max_calls=1,
            excluded_exceptions=(ValueError,),
            fallback_function=fallback,
        )
        assert cfg.name == "custom"
        assert cfg.failure_threshold == 3
        assert cfg.call_timeout_seconds == 5.0
        assert cfg.excluded_exceptions == (ValueError,)
        assert cfg.fallback_function is fallback


# -- CircuitBreaker init -----------------------------------------------------


class TestCircuitBreakerInit:
    def test_init(self):
        cfg = CircuitBreakerConfig(name="test-breaker")
        cb = CircuitBreaker(cfg)
        assert cb.name == "test-breaker"
        assert cb.config is cfg

    def test_initial_state_closed(self):
        cfg = CircuitBreakerConfig(name="init-test")
        cb = CircuitBreaker(cfg)
        assert cb.state == CircuitState.CLOSED

    def test_state_machine_configured(self):
        cfg = CircuitBreakerConfig(
            name="sm-test", failure_threshold=10, success_threshold=5
        )
        cb = CircuitBreaker(cfg)
        assert cb.state_machine.failure_threshold == 10
        assert cb.state_machine.success_threshold == 5


# -- CircuitBreaker.call (sync) ----------------------------------------------


class TestCircuitBreakerCall:
    def test_success(self):
        cfg = CircuitBreakerConfig(name="call-success")
        cb = CircuitBreaker(cfg)
        result = cb.call(lambda: 42)
        assert result == 42

    def test_passes_args(self):
        cfg = CircuitBreakerConfig(name="call-args")
        cb = CircuitBreaker(cfg)
        result = cb.call(lambda x, y: x + y, 3, 4)
        assert result == 7

    def test_passes_kwargs(self):
        cfg = CircuitBreakerConfig(name="call-kwargs")
        cb = CircuitBreaker(cfg)
        result = cb.call(lambda x, y=10: x + y, 5, y=20)
        assert result == 25

    def test_records_success(self):
        cfg = CircuitBreakerConfig(name="record-success")
        cb = CircuitBreaker(cfg)
        cb.call(lambda: "ok")
        assert cb.state_machine.metrics.successful_requests == 1
        assert cb.state_machine.metrics.total_requests == 1

    def test_records_failure(self):
        cfg = CircuitBreakerConfig(name="record-failure")
        cb = CircuitBreaker(cfg)
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
        assert cb.state_machine.metrics.failed_requests == 1

    def test_failure_raises(self):
        cfg = CircuitBreakerConfig(name="failure-raises")
        cb = CircuitBreaker(cfg)

        def failing():
            raise RuntimeError("service down")

        with pytest.raises(RuntimeError, match="service down"):
            cb.call(failing)

    def test_open_circuit_rejects(self):
        cfg = CircuitBreakerConfig(name="open-reject", failure_threshold=2)
        cb = CircuitBreaker(cfg)

        def failing():
            raise RuntimeError("fail")

        # Trip the breaker
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(failing)

        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "should not run")

    def test_open_circuit_records_rejection(self):
        cfg = CircuitBreakerConfig(name="rejection-count", failure_threshold=1)
        cb = CircuitBreaker(cfg)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: None)
        assert cb.state_machine.metrics.rejected_requests == 1

    def test_fallback_on_open(self):
        cfg = CircuitBreakerConfig(
            name="fallback-open",
            failure_threshold=1,
            fallback_function=lambda: "fallback-value",
        )
        cb = CircuitBreaker(cfg)

        # First call fails but fallback catches it
        result = cb.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
        assert result == "fallback-value"
        assert cb.state == CircuitState.OPEN

        # Now open, fallback should be used on rejection too
        result = cb.call(lambda: "unreachable")
        assert result == "fallback-value"

    def test_fallback_on_failure(self):
        cfg = CircuitBreakerConfig(
            name="fallback-fail",
            fallback_function=lambda: "recovered",
        )
        cb = CircuitBreaker(cfg)

        def failing():
            raise RuntimeError("boom")

        result = cb.call(failing)
        assert result == "recovered"

    def test_excluded_exception_not_counted(self):
        cfg = CircuitBreakerConfig(
            name="excluded",
            excluded_exceptions=(ValueError,),
        )
        cb = CircuitBreaker(cfg)

        def raises_value_error():
            raise ValueError("excluded")

        with pytest.raises(ValueError):
            cb.call(raises_value_error)

        # Excluded exception should NOT be counted as failure
        assert cb.state_machine.metrics.failed_requests == 0
        assert cb.state_machine.metrics.successful_requests == 0

    def test_non_excluded_exception_counted(self):
        cfg = CircuitBreakerConfig(
            name="non-excluded",
            excluded_exceptions=(ValueError,),
        )
        cb = CircuitBreaker(cfg)

        with pytest.raises(TypeError):
            cb.call(lambda: (_ for _ in ()).throw(TypeError("not excluded")))

        assert cb.state_machine.metrics.failed_requests == 1


# -- CircuitBreaker.__call__ context manager ---------------------------------


class TestCircuitBreakerContextManager:
    def test_success(self):
        cfg = CircuitBreakerConfig(name="ctx-success")
        cb = CircuitBreaker(cfg)
        with cb():
            result = 42
        assert result == 42
        assert cb.state_machine.metrics.successful_requests == 1

    def test_failure(self):
        cfg = CircuitBreakerConfig(name="ctx-failure")
        cb = CircuitBreaker(cfg)
        with pytest.raises(ValueError):
            with cb():
                raise ValueError("ctx fail")
        assert cb.state_machine.metrics.failed_requests == 1

    def test_open_rejects(self):
        cfg = CircuitBreakerConfig(name="ctx-open", failure_threshold=1)
        cb = CircuitBreaker(cfg)

        with pytest.raises(RuntimeError):
            with cb():
                raise RuntimeError("trip it")

        with pytest.raises(CircuitOpenError):
            with cb():
                pass

    def test_excluded_exception(self):
        cfg = CircuitBreakerConfig(
            name="ctx-excluded",
            excluded_exceptions=(ValueError,),
        )
        cb = CircuitBreaker(cfg)

        with pytest.raises(ValueError):
            with cb():
                raise ValueError("excluded")

        assert cb.state_machine.metrics.failed_requests == 0


# -- open / close / reset / get_status --------------------------------------


class TestManualOverrides:
    def test_open(self):
        cfg = CircuitBreakerConfig(name="manual-open")
        cb = CircuitBreaker(cfg)
        cb.open("Testing")
        assert cb.state == CircuitState.OPEN

    def test_close(self):
        cfg = CircuitBreakerConfig(name="manual-close", failure_threshold=1)
        cb = CircuitBreaker(cfg)
        cb.open("test")
        cb.close("Recovery")
        assert cb.state == CircuitState.CLOSED

    def test_reset(self):
        cfg = CircuitBreakerConfig(name="reset-test", failure_threshold=1)
        cb = CircuitBreaker(cfg)

        # Generate some state
        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.state_machine.metrics.total_requests == 0


class TestGetStatus:
    def test_has_name(self):
        cfg = CircuitBreakerConfig(name="status-test")
        cb = CircuitBreaker(cfg)
        status = cb.get_status()
        assert status["name"] == "status-test"

    def test_has_state(self):
        cfg = CircuitBreakerConfig(name="state-status")
        cb = CircuitBreaker(cfg)
        status = cb.get_status()
        assert status["state"] == "closed"

    def test_reflects_open(self):
        cfg = CircuitBreakerConfig(name="open-status", failure_threshold=1)
        cb = CircuitBreaker(cfg)
        cb.open("test")
        status = cb.get_status()
        assert status["state"] == "open"

    def test_includes_metrics(self):
        cfg = CircuitBreakerConfig(name="metrics-status")
        cb = CircuitBreaker(cfg)
        cb.call(lambda: "ok")
        status = cb.get_status()
        assert status["total_requests"] == 1
        assert status["successful_requests"] == 1
