"""
Circuit Breaker Registry.

Manages multiple circuit breakers for different services:

1. Central registry of all breakers
2. Default configurations
3. Breaker lifecycle management
4. Bulk operations (reset all, get all statuses)
"""

import logging

from app.resilience.circuit_breaker.breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
)

logger = logging.getLogger(__name__)


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Provides centralized management of circuit breakers for different services.

    Example:
        registry = CircuitBreakerRegistry()

        # Register breakers
        registry.register(
            "database",
            failure_threshold=5,
            timeout_seconds=60,
        )
        registry.register(
            "external_api",
            failure_threshold=3,
            timeout_seconds=30,
        )

        # Get and use breakers
        db_breaker = registry.get("database")
        async with db_breaker.async_call():
            await db_operation()

        # Get all statuses
        statuses = registry.get_all_statuses()
    """

    def __init__(self):
        """Initialize the registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._default_config = CircuitBreakerConfig(
            name="default",
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0,
            half_open_max_calls=3,
        )
        logger.info("Circuit breaker registry initialized")

    def set_default_config(self, config: CircuitBreakerConfig):
        """
        Set default configuration for new breakers.

        Args:
            config: Default configuration
        """
        self._default_config = config
        logger.info("Default circuit breaker configuration updated")

    def register(
        self,
        name: str,
        failure_threshold: int | None = None,
        success_threshold: int | None = None,
        timeout_seconds: float | None = None,
        call_timeout_seconds: float | None = None,
        half_open_max_calls: int | None = None,
        excluded_exceptions: tuple[type[Exception], ...] | None = None,
        fallback_function: callable | None = None,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.

        Args:
            name: Unique name for the breaker
            failure_threshold: Failures before opening (overrides default)
            success_threshold: Successes to close (overrides default)
            timeout_seconds: Recovery timeout (overrides default)
            call_timeout_seconds: Individual call timeout
            half_open_max_calls: Max concurrent half-open calls
            excluded_exceptions: Exceptions to exclude from failure count
            fallback_function: Fallback function when circuit is open
            config: Full configuration object (overrides all individual params)

        Returns:
            The registered circuit breaker

        Raises:
            ValueError: If breaker already exists
        """
        if name in self._breakers:
            raise ValueError(f"Circuit breaker '{name}' already registered")

        # Use provided config or build from params
        if config:
            breaker_config = config
        else:
            breaker_config = CircuitBreakerConfig(
                name=name,
                failure_threshold=(
                    failure_threshold or self._default_config.failure_threshold
                ),
                success_threshold=(
                    success_threshold or self._default_config.success_threshold
                ),
                timeout_seconds=(
                    timeout_seconds or self._default_config.timeout_seconds
                ),
                call_timeout_seconds=call_timeout_seconds,
                half_open_max_calls=(
                    half_open_max_calls or self._default_config.half_open_max_calls
                ),
                excluded_exceptions=excluded_exceptions or (),
                fallback_function=fallback_function,
            )

        breaker = CircuitBreaker(breaker_config)
        self._breakers[name] = breaker

        logger.info(
            f"Registered circuit breaker '{name}': "
            f"failure_threshold={breaker_config.failure_threshold}, "
            f"timeout={breaker_config.timeout_seconds}s"
        )

        return breaker

    def get(self, name: str) -> CircuitBreaker:
        """
        Get a circuit breaker by name.

        Args:
            name: Name of the breaker

        Returns:
            The circuit breaker

        Raises:
            KeyError: If breaker not found
        """
        if name not in self._breakers:
            raise KeyError(f"Circuit breaker '{name}' not found")
        return self._breakers[name]

    def get_or_create(
        self,
        name: str,
        **kwargs,
    ) -> CircuitBreaker:
        """
        Get existing breaker or create new one.

        Args:
            name: Name of the breaker
            **kwargs: Configuration params (see register())

        Returns:
            The circuit breaker
        """
        try:
            return self.get(name)
        except KeyError:
            return self.register(name, **kwargs)

    def exists(self, name: str) -> bool:
        """
        Check if a breaker exists.

        Args:
            name: Name of the breaker

        Returns:
            True if breaker exists
        """
        return name in self._breakers

    def unregister(self, name: str):
        """
        Remove a circuit breaker.

        Args:
            name: Name of the breaker

        Raises:
            KeyError: If breaker not found
        """
        if name not in self._breakers:
            raise KeyError(f"Circuit breaker '{name}' not found")

        del self._breakers[name]
        logger.info(f"Unregistered circuit breaker '{name}'")

    def get_all_statuses(self) -> dict[str, dict]:
        """
        Get status of all circuit breakers.

        Returns:
            Dictionary mapping names to status dicts
        """
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers to initial state."""
        for breaker in self._breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")

    def open_all(self, reason: str = "Bulk manual override"):
        """
        Open all circuit breakers.

        Args:
            reason: Reason for opening
        """
        for breaker in self._breakers.values():
            breaker.open(reason)
        logger.warning(f"All circuit breakers opened: {reason}")

    def close_all(self, reason: str = "Bulk manual override"):
        """
        Close all circuit breakers.

        Args:
            reason: Reason for closing
        """
        for breaker in self._breakers.values():
            breaker.close(reason)
        logger.info(f"All circuit breakers closed: {reason}")

    def list_breakers(self) -> list[str]:
        """
        Get list of all registered breaker names.

        Returns:
            List of breaker names
        """
        return list(self._breakers.keys())

    def get_open_breakers(self) -> list[str]:
        """
        Get list of breakers in OPEN state.

        Returns:
            List of open breaker names
        """
        from app.resilience.circuit_breaker.states import CircuitState

        return [
            name
            for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.OPEN
        ]

    def get_half_open_breakers(self) -> list[str]:
        """
        Get list of breakers in HALF_OPEN state.

        Returns:
            List of half-open breaker names
        """
        from app.resilience.circuit_breaker.states import CircuitState

        return [
            name
            for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.HALF_OPEN
        ]

    def health_check(self) -> dict:
        """
        Perform health check on all breakers.

        Returns:
            Health check results
        """
        statuses = self.get_all_statuses()
        open_breakers = self.get_open_breakers()
        half_open_breakers = self.get_half_open_breakers()

        total_requests = sum(status["total_requests"] for status in statuses.values())
        total_failures = sum(status["failed_requests"] for status in statuses.values())
        total_rejections = sum(
            status["rejected_requests"] for status in statuses.values()
        )

        return {
            "total_breakers": len(self._breakers),
            "open_breakers": len(open_breakers),
            "half_open_breakers": len(half_open_breakers),
            "closed_breakers": (
                len(self._breakers) - len(open_breakers) - len(half_open_breakers)
            ),
            "open_breaker_names": open_breakers,
            "half_open_breaker_names": half_open_breakers,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "total_rejections": total_rejections,
            "overall_failure_rate": (
                total_failures / total_requests if total_requests > 0 else 0.0
            ),
        }


# Global registry instance
_registry: CircuitBreakerRegistry | None = None


def get_registry() -> CircuitBreakerRegistry:
    """
    Get or create the global circuit breaker registry.

    Returns:
        The global registry instance
    """
    global _registry
    if _registry is None:
        _registry = CircuitBreakerRegistry()
    return _registry


def setup_registry() -> CircuitBreakerRegistry:
    """
    Set up the global registry.

    Call during app startup to initialize the registry.

    Returns:
        The initialized registry
    """
    global _registry
    _registry = CircuitBreakerRegistry()
    return _registry
