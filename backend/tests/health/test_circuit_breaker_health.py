"""
Tests for CircuitBreakerHealthCheck implementation.

Tests coverage for circuit breaker health monitoring including:
- Health check with all breakers closed (healthy)
- Health check with some breakers open (degraded)
- Health check with critical breakers open (unhealthy)
- Individual breaker status reporting
- Timeout handling
- Error handling
"""

import pytest

from app.health.checks.circuit_breaker import CircuitBreakerHealthCheck
from app.resilience.circuit_breaker.breaker import CircuitBreakerConfig
from app.resilience.circuit_breaker.registry import CircuitBreakerRegistry, get_registry
from app.resilience.circuit_breaker.states import CircuitState


@pytest.fixture
def reset_registry():
    """Reset circuit breaker registry before and after each test."""
    # Reset before test
    from app.resilience.circuit_breaker import registry as reg_module

    reg_module._registry = None

    yield

    # Reset after test
    reg_module._registry = None


@pytest.fixture
def health_checker():
    """Create a CircuitBreakerHealthCheck instance."""
    return CircuitBreakerHealthCheck(timeout=5.0)


@pytest.fixture
def sample_breakers(reset_registry):
    """Create sample circuit breakers for testing."""
    registry = get_registry()

    # Register a few breakers
    registry.register("database", failure_threshold=5, timeout_seconds=60)
    registry.register("redis", failure_threshold=3, timeout_seconds=30)
    registry.register("external_api", failure_threshold=3, timeout_seconds=30)
    registry.register("non_critical_service", failure_threshold=5, timeout_seconds=60)

    return registry


class TestCircuitBreakerHealthCheck:
    """Test suite for CircuitBreakerHealthCheck."""

    @pytest.mark.asyncio
    async def test_check_all_breakers_closed_healthy(
        self, health_checker, sample_breakers
    ):
        """Test health check with all breakers closed returns healthy status."""
        result = await health_checker.check()

        assert result["status"] == "healthy"
        assert result["total_breakers"] == 4
        assert result["open_breakers"] == 0
        assert result["half_open_breakers"] == 0
        assert result["closed_breakers"] == 4
        assert result["overall_failure_rate"] == 0.0
        assert "response_time_ms" in result
        assert "breaker_details" in result

    @pytest.mark.asyncio
    async def test_check_some_breakers_open_degraded(
        self, health_checker, sample_breakers
    ):
        """Test health check with some non-critical breakers open returns degraded."""
        # Open a non-critical breaker
        breaker = sample_breakers.get("non_critical_service")
        breaker.open("Test: Opening for degraded test")

        result = await health_checker.check()

        assert result["status"] == "degraded"
        assert result["total_breakers"] == 4
        assert result["open_breakers"] == 1
        assert result["closed_breakers"] == 3
        assert "non_critical_service" in result["open_breaker_names"]
        assert "warning" in result
        assert "circuit breaker(s) open" in result["warning"]

    @pytest.mark.asyncio
    async def test_check_critical_breaker_open_unhealthy(
        self, health_checker, sample_breakers
    ):
        """Test health check with critical breaker open returns unhealthy."""
        # Open a critical breaker (database)
        breaker = sample_breakers.get("database")
        breaker.open("Test: Opening critical breaker")

        result = await health_checker.check()

        assert result["status"] == "unhealthy"
        assert result["open_breakers"] == 1
        assert "database" in result["open_breaker_names"]

    @pytest.mark.asyncio
    async def test_check_all_breakers_open_unhealthy(
        self, health_checker, sample_breakers
    ):
        """Test health check with all breakers open returns unhealthy."""
        # Open all breakers
        sample_breakers.open_all("Test: Opening all breakers")

        result = await health_checker.check()

        assert result["status"] == "unhealthy"
        assert result["total_breakers"] == 4
        assert result["open_breakers"] == 4
        assert result["closed_breakers"] == 0

    @pytest.mark.asyncio
    async def test_check_half_open_breakers_degraded(
        self, health_checker, sample_breakers
    ):
        """Test health check with half-open breakers returns degraded."""
        # Open a breaker and then attempt recovery
        breaker = sample_breakers.get("non_critical_service")
        breaker.open("Test: Opening for half-open test")

        # Force to half-open state
        breaker.state_machine._transition_to_half_open()

        result = await health_checker.check()

        assert result["status"] == "degraded"
        assert result["half_open_breakers"] == 1
        assert "non_critical_service" in result["half_open_breaker_names"]
        assert "warning" in result

    @pytest.mark.asyncio
    async def test_check_breaker_details_included(
        self, health_checker, sample_breakers
    ):
        """Test health check includes detailed breaker information."""
        # Record some failures on a breaker
        breaker = sample_breakers.get("database")
        for _ in range(3):
            breaker.state_machine.record_failure()

        result = await health_checker.check()

        assert "breaker_details" in result
        assert "database" in result["breaker_details"]

        db_details = result["breaker_details"]["database"]
        assert db_details["state"] == "CLOSED"
        assert db_details["failure_count"] == 3
        assert db_details["total_requests"] > 0
        assert "last_state_change" in db_details

    @pytest.mark.asyncio
    async def test_check_failure_rate_calculation(
        self, health_checker, sample_breakers
    ):
        """Test health check calculates overall failure rate correctly."""
        # Record some successes and failures
        breaker = sample_breakers.get("database")
        for _ in range(2):
            breaker.state_machine.record_success()
        for _ in range(3):
            breaker.state_machine.record_failure()

        result = await health_checker.check()

        assert result["total_requests"] > 0
        assert result["total_failures"] == 3
        assert result["overall_failure_rate"] > 0

    @pytest.mark.asyncio
    async def test_check_no_breakers_registered_healthy(
        self, health_checker, reset_registry
    ):
        """Test health check with no breakers registered returns healthy."""
        result = await health_checker.check()

        assert result["status"] == "healthy"
        assert result["total_breakers"] == 0
        assert result["open_breakers"] == 0

    @pytest.mark.asyncio
    async def test_check_response_time_measured(self, health_checker, sample_breakers):
        """Test health check measures response time."""
        result = await health_checker.check()

        assert "response_time_ms" in result
        assert result["response_time_ms"] > 0
        assert result["response_time_ms"] < 1000  # Should be fast

    @pytest.mark.asyncio
    async def test_check_timeout_handling(self, reset_registry):
        """Test health check handles timeout properly."""
        # Create health checker with very short timeout
        health_checker = CircuitBreakerHealthCheck(timeout=0.001)

        # Register many breakers (might cause timeout)
        registry = get_registry()
        for i in range(100):
            registry.register(f"breaker_{i}", failure_threshold=5)

        result = await health_checker.check()

        # Should either succeed or return timeout error
        if result["status"] == "unhealthy":
            assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_check_critical_breakers_only(self, health_checker, sample_breakers):
        """Test critical breakers check returns only critical breaker status."""
        result = await health_checker.check_critical_breakers()

        assert "status" in result
        assert "critical_breakers" in result
        assert result["status"] == "healthy"
        assert result["any_critical_open"] is False

        # Check that only critical breakers are included
        critical_breakers = result["critical_breakers"]
        assert "database" in critical_breakers
        assert "redis" in critical_breakers
        assert "external_api" in critical_breakers
        assert "non_critical_service" not in critical_breakers

    @pytest.mark.asyncio
    async def test_check_critical_breakers_with_open_critical(
        self, health_checker, sample_breakers
    ):
        """Test critical breakers check detects open critical breakers."""
        # Open a critical breaker
        breaker = sample_breakers.get("redis")
        breaker.open("Test: Opening critical breaker")

        result = await health_checker.check_critical_breakers()

        assert result["status"] == "unhealthy"
        assert result["any_critical_open"] is True
        assert result["critical_breakers"]["redis"]["is_open"] is True

    @pytest.mark.asyncio
    async def test_check_rejection_statistics(self, health_checker, sample_breakers):
        """Test health check includes rejection statistics."""
        # Open a breaker and trigger rejections
        breaker = sample_breakers.get("database")
        breaker.open("Test: Trigger rejections")

        # Attempt to use the breaker (will be rejected)
        for _ in range(5):
            breaker.state_machine.record_rejection()

        result = await health_checker.check()

        assert result["total_rejections"] == 5

    @pytest.mark.asyncio
    async def test_check_warning_message_format(self, health_checker, sample_breakers):
        """Test warning message format for degraded status."""
        # Open one breaker
        sample_breakers.get("non_critical_service").open("Test")

        # Set one to half-open
        breaker = sample_breakers.get("external_api")
        breaker.open("Test")
        breaker.state_machine._transition_to_half_open()

        result = await health_checker.check()

        assert result["status"] == "degraded"
        assert "warning" in result

        warning = result["warning"]
        assert "circuit breaker(s) open" in warning
        assert "circuit breaker(s) half-open" in warning


class TestCircuitBreakerHealthCheckIntegration:
    """Integration tests for circuit breaker health check with health aggregator."""

    @pytest.mark.asyncio
    async def test_health_aggregator_includes_circuit_breakers(self, sample_breakers):
        """Test health aggregator includes circuit breaker check."""
        from app.health.aggregator import HealthAggregator

        aggregator = HealthAggregator(enable_history=False, timeout=10.0)
        result = await aggregator.check_detailed()

        assert "circuit_breakers" in result.services
        circuit_breaker_result = result.services["circuit_breakers"]
        assert circuit_breaker_result.service == "circuit_breakers"
        assert circuit_breaker_result.status in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_check_service_circuit_breakers(self, sample_breakers):
        """Test checking circuit breakers as a specific service."""
        from app.health.aggregator import HealthAggregator

        aggregator = HealthAggregator(enable_history=False, timeout=10.0)
        result = await aggregator.check_service("circuit_breakers")

        assert result.service == "circuit_breakers"
        assert result.status in ["healthy", "degraded", "unhealthy"]
        assert "breaker_details" in result.details

    @pytest.mark.asyncio
    async def test_overall_status_degraded_with_open_breakers(self, sample_breakers):
        """Test overall health status is degraded when breakers are open."""
        from app.health.aggregator import HealthAggregator

        # Open a non-critical breaker
        sample_breakers.get("non_critical_service").open("Test")

        aggregator = HealthAggregator(enable_history=False, timeout=10.0)
        result = await aggregator.check_detailed()

        # Circuit breaker service should be degraded
        circuit_breaker_result = result.services["circuit_breakers"]
        assert circuit_breaker_result.status == "degraded"

    @pytest.mark.asyncio
    async def test_overall_status_unhealthy_with_critical_breakers(
        self, sample_breakers
    ):
        """Test overall health status affected by critical breakers."""
        from app.health.aggregator import HealthAggregator

        # Open a critical breaker
        sample_breakers.get("database").open("Test")

        aggregator = HealthAggregator(enable_history=False, timeout=10.0)
        result = await aggregator.check_detailed()

        # Circuit breaker service should be unhealthy
        circuit_breaker_result = result.services["circuit_breakers"]
        assert circuit_breaker_result.status == "unhealthy"


class TestCircuitBreakerHealthCheckEdgeCases:
    """Edge case tests for circuit breaker health check."""

    @pytest.mark.asyncio
    async def test_check_with_exception_handling(self, health_checker, reset_registry):
        """Test health check handles exceptions gracefully."""
        # This should not raise an exception even if registry is in weird state
        result = await health_checker.check()

        assert "status" in result
        assert result["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_check_with_very_short_timeout(self, health_checker, sample_breakers):
        """Test health check with very short timeout."""
        health_checker.timeout = 0.0001  # Extremely short timeout

        result = await health_checker.check()

        # Should handle timeout gracefully
        assert "status" in result
        # Might timeout, but should not crash
        if result["status"] == "unhealthy":
            assert "error" in result

    @pytest.mark.asyncio
    async def test_check_multiple_times_consistency(
        self, health_checker, sample_breakers
    ):
        """Test multiple health checks return consistent results."""
        results = []
        for _ in range(5):
            result = await health_checker.check()
            results.append(result)

        # All should have same status (assuming no changes)
        statuses = [r["status"] for r in results]
        assert len(set(statuses)) == 1  # All same status

    @pytest.mark.asyncio
    async def test_check_with_mixed_breaker_states(
        self, health_checker, sample_breakers
    ):
        """Test health check with breakers in mixed states."""
        # Create a mixed scenario
        sample_breakers.get("database").close("Test")  # Closed
        sample_breakers.get("redis").open("Test")  # Open (critical)
        breaker = sample_breakers.get("external_api")
        breaker.open("Test")
        breaker.state_machine._transition_to_half_open()  # Half-open (critical)
        sample_breakers.get("non_critical_service").close("Test")  # Closed

        result = await health_checker.check()

        # Should be unhealthy because critical breakers are open/half-open
        assert result["status"] == "unhealthy"
        assert result["open_breakers"] > 0 or result["half_open_breakers"] > 0
