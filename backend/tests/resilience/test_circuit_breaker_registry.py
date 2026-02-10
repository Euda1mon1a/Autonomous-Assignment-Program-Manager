"""Tests for circuit breaker registry (pure logic, no DB)."""

import pytest

from app.resilience.circuit_breaker.breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
)
from app.resilience.circuit_breaker.registry import (
    CircuitBreakerRegistry,
    get_registry,
    setup_registry,
)
from app.resilience.circuit_breaker.states import CircuitState


# -- CircuitBreakerRegistry init ---------------------------------------------


class TestRegistryInit:
    def test_empty_on_init(self):
        reg = CircuitBreakerRegistry()
        assert reg.list_breakers() == []

    def test_default_config_set(self):
        reg = CircuitBreakerRegistry()
        assert reg._default_config.failure_threshold == 5
        assert reg._default_config.success_threshold == 2
        assert reg._default_config.timeout_seconds == 60.0


# -- register ----------------------------------------------------------------


class TestRegister:
    def test_register_returns_breaker(self):
        reg = CircuitBreakerRegistry()
        breaker = reg.register("test-svc")
        assert isinstance(breaker, CircuitBreaker)

    def test_register_with_name(self):
        reg = CircuitBreakerRegistry()
        breaker = reg.register("my-api")
        assert breaker.name == "my-api"

    def test_register_custom_params(self):
        reg = CircuitBreakerRegistry()
        breaker = reg.register("custom", failure_threshold=10, timeout_seconds=30.0)
        assert breaker.config.failure_threshold == 10
        assert breaker.config.timeout_seconds == 30.0

    def test_register_with_config_object(self):
        reg = CircuitBreakerRegistry()
        cfg = CircuitBreakerConfig(name="full-cfg", failure_threshold=7)
        breaker = reg.register("full-cfg", config=cfg)
        assert breaker.config.failure_threshold == 7

    def test_duplicate_name_raises(self):
        reg = CircuitBreakerRegistry()
        reg.register("dup")
        with pytest.raises(ValueError, match="already registered"):
            reg.register("dup")

    def test_register_with_fallback(self):
        reg = CircuitBreakerRegistry()

        def fb():
            return "fb"

        breaker = reg.register("fb-test", fallback_function=fb)
        assert breaker.config.fallback_function is fb

    def test_register_with_excluded_exceptions(self):
        reg = CircuitBreakerRegistry()
        breaker = reg.register("exc-test", excluded_exceptions=(ValueError,))
        assert breaker.config.excluded_exceptions == (ValueError,)


# -- get ---------------------------------------------------------------------


class TestGet:
    def test_get_registered(self):
        reg = CircuitBreakerRegistry()
        reg.register("svc-a")
        breaker = reg.get("svc-a")
        assert breaker.name == "svc-a"

    def test_get_not_found_raises(self):
        reg = CircuitBreakerRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.get("nonexistent")


# -- get_or_create -----------------------------------------------------------


class TestGetOrCreate:
    def test_creates_new(self):
        reg = CircuitBreakerRegistry()
        breaker = reg.get_or_create("new-svc", failure_threshold=3)
        assert breaker.name == "new-svc"
        assert breaker.config.failure_threshold == 3

    def test_returns_existing(self):
        reg = CircuitBreakerRegistry()
        b1 = reg.register("existing")
        b2 = reg.get_or_create("existing")
        assert b1 is b2


# -- exists ------------------------------------------------------------------


class TestExists:
    def test_exists_true(self):
        reg = CircuitBreakerRegistry()
        reg.register("check-me")
        assert reg.exists("check-me") is True

    def test_exists_false(self):
        reg = CircuitBreakerRegistry()
        assert reg.exists("nope") is False


# -- unregister --------------------------------------------------------------


class TestUnregister:
    def test_unregister(self):
        reg = CircuitBreakerRegistry()
        reg.register("remove-me")
        reg.unregister("remove-me")
        assert reg.exists("remove-me") is False

    def test_unregister_not_found_raises(self):
        reg = CircuitBreakerRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.unregister("missing")


# -- list_breakers -----------------------------------------------------------


class TestListBreakers:
    def test_empty(self):
        reg = CircuitBreakerRegistry()
        assert reg.list_breakers() == []

    def test_multiple(self):
        reg = CircuitBreakerRegistry()
        reg.register("a")
        reg.register("b")
        reg.register("c")
        names = reg.list_breakers()
        assert set(names) == {"a", "b", "c"}


# -- get_all_statuses --------------------------------------------------------


class TestGetAllStatuses:
    def test_empty(self):
        reg = CircuitBreakerRegistry()
        assert reg.get_all_statuses() == {}

    def test_returns_dict_per_breaker(self):
        reg = CircuitBreakerRegistry()
        reg.register("x")
        reg.register("y")
        statuses = reg.get_all_statuses()
        assert "x" in statuses
        assert "y" in statuses
        assert statuses["x"]["name"] == "x"

    def test_status_has_state(self):
        reg = CircuitBreakerRegistry()
        reg.register("z")
        statuses = reg.get_all_statuses()
        assert statuses["z"]["state"] == "closed"


# -- bulk operations ---------------------------------------------------------


class TestBulkOperations:
    def test_reset_all(self):
        reg = CircuitBreakerRegistry()
        b = reg.register("reset-test", failure_threshold=1)
        with pytest.raises(RuntimeError):
            b.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
        assert b.state_machine.metrics.failed_requests == 1
        reg.reset_all()
        assert b.state_machine.metrics.failed_requests == 0

    def test_open_all(self):
        reg = CircuitBreakerRegistry()
        reg.register("o1")
        reg.register("o2")
        reg.open_all("test")
        for name in ["o1", "o2"]:
            assert reg.get(name).state == CircuitState.OPEN

    def test_close_all(self):
        reg = CircuitBreakerRegistry()
        b1 = reg.register("c1", failure_threshold=1)
        b2 = reg.register("c2", failure_threshold=1)
        b1.open("test")
        b2.open("test")
        reg.close_all("recovery")
        assert b1.state == CircuitState.CLOSED
        assert b2.state == CircuitState.CLOSED


# -- get_open_breakers / get_half_open_breakers ------------------------------


class TestStateFilters:
    def test_get_open_breakers_empty(self):
        reg = CircuitBreakerRegistry()
        reg.register("healthy")
        assert reg.get_open_breakers() == []

    def test_get_open_breakers(self):
        reg = CircuitBreakerRegistry()
        reg.register("closed-svc")
        b = reg.register("open-svc", failure_threshold=1)
        b.open("test")
        assert reg.get_open_breakers() == ["open-svc"]

    def test_get_half_open_breakers_empty(self):
        reg = CircuitBreakerRegistry()
        reg.register("normal")
        assert reg.get_half_open_breakers() == []

    def test_get_half_open_breakers(self):
        reg = CircuitBreakerRegistry()
        b = reg.register("ho-svc")
        b.state_machine.current_state = CircuitState.HALF_OPEN
        assert reg.get_half_open_breakers() == ["ho-svc"]


# -- health_check ------------------------------------------------------------


class TestHealthCheck:
    def test_empty_registry(self):
        reg = CircuitBreakerRegistry()
        health = reg.health_check()
        assert health["total_breakers"] == 0
        assert health["overall_failure_rate"] == 0.0

    def test_all_closed(self):
        reg = CircuitBreakerRegistry()
        reg.register("h1")
        reg.register("h2")
        health = reg.health_check()
        assert health["total_breakers"] == 2
        assert health["closed_breakers"] == 2
        assert health["open_breakers"] == 0
        assert health["half_open_breakers"] == 0

    def test_with_requests(self):
        reg = CircuitBreakerRegistry()
        b = reg.register("active")
        b.call(lambda: "ok")
        b.call(lambda: "ok")
        health = reg.health_check()
        assert health["total_requests"] == 2
        assert health["total_failures"] == 0

    def test_with_failures(self):
        reg = CircuitBreakerRegistry()
        b = reg.register("failing")
        try:
            b.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        health = reg.health_check()
        assert health["total_failures"] == 1
        assert health["overall_failure_rate"] == 1.0

    def test_has_expected_keys(self):
        reg = CircuitBreakerRegistry()
        health = reg.health_check()
        expected = {
            "total_breakers",
            "open_breakers",
            "half_open_breakers",
            "closed_breakers",
            "open_breaker_names",
            "half_open_breaker_names",
            "total_requests",
            "total_failures",
            "total_rejections",
            "overall_failure_rate",
        }
        assert set(health.keys()) == expected


# -- set_default_config ------------------------------------------------------


class TestSetDefaultConfig:
    def test_set_default(self):
        reg = CircuitBreakerRegistry()
        new_default = CircuitBreakerConfig(name="new-default", failure_threshold=10)
        reg.set_default_config(new_default)
        breaker = reg.register("uses-default")
        assert breaker.config.failure_threshold == 10


# -- Global functions --------------------------------------------------------


class TestGlobalFunctions:
    def test_get_registry_returns_instance(self):
        reg = get_registry()
        assert isinstance(reg, CircuitBreakerRegistry)

    def test_setup_registry_returns_fresh(self):
        reg = setup_registry()
        assert isinstance(reg, CircuitBreakerRegistry)
        assert reg.list_breakers() == []
