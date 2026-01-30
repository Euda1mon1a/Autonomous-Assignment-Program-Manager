"""
Dynamic routing for API gateway.

Provides dynamic route registration and request routing based on configurable rules.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastapi import Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Routing strategy types."""

    PATH_PREFIX = "path_prefix"
    REGEX = "regex"
    HEADER = "header"
    METHOD = "method"
    COMPOSITE = "composite"


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategy types."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"
    IP_HASH = "ip_hash"


class RouteConfig(BaseModel):
    """Configuration for a route."""

    name: str = Field(..., description="Unique name for the route")
    pattern: str = Field(..., description="Pattern to match (path, regex, etc.)")
    strategy: RoutingStrategy = Field(
        default=RoutingStrategy.PATH_PREFIX,
        description="Routing strategy to use",
    )
    target_services: list[str] = Field(
        default_factory=list,
        description="List of target service URLs",
    )
    load_balancing: LoadBalancingStrategy = Field(
        default=LoadBalancingStrategy.ROUND_ROBIN,
        description="Load balancing strategy",
    )
    priority: int = Field(
        default=100,
        description="Route priority (lower = higher priority)",
    )
    enabled: bool = Field(default=True, description="Whether route is enabled")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Headers to match for header-based routing",
    )
    methods: list[str] = Field(
        default_factory=list,
        description="HTTP methods to match",
    )
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds",
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts on failure",
    )
    circuit_breaker_threshold: int = Field(
        default=5,
        description="Consecutive failures before circuit breaker opens",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the route",
    )

    class Config:
        use_enum_values = True


@dataclass
class RouteRule:
    """Internal representation of a routing rule."""

    config: RouteConfig
    matcher: Callable[[Request], bool]
    current_index: int = 0
    connection_counts: dict[str, int] = field(default_factory=dict)
    failure_counts: dict[str, int] = field(default_factory=dict)
    circuit_open: dict[str, bool] = field(default_factory=dict)


class DynamicRouter:
    """
    Dynamic router for API gateway.

    Provides dynamic route registration and request routing based on configurable rules.
    Supports multiple routing strategies and load balancing algorithms.
    """

    def __init__(self) -> None:
        """Initialize the dynamic router."""
        self._routes: list[RouteRule] = []
        self._route_cache: dict[str, RouteRule] = {}
        logger.info("Dynamic router initialized")

    def register_route(self, config: RouteConfig) -> None:
        """
        Register a new route with the router.

        Args:
            config: Route configuration

        Raises:
            ValueError: If route with same name already exists
        """
        # Check for duplicate names
        if any(r.config.name == config.name for r in self._routes):
            raise ValueError(f"Route with name '{config.name}' already exists")

            # Create matcher based on strategy
        matcher = self._create_matcher(config)

        # Initialize connection tracking
        connection_counts = dict.fromkeys(config.target_services, 0)
        failure_counts = dict.fromkeys(config.target_services, 0)
        circuit_open = dict.fromkeys(config.target_services, False)

        # Create route rule
        rule = RouteRule(
            config=config,
            matcher=matcher,
            connection_counts=connection_counts,
            failure_counts=failure_counts,
            circuit_open=circuit_open,
        )

        # Add to routes and sort by priority
        self._routes.append(rule)
        self._routes.sort(key=lambda r: r.config.priority)

        # Clear cache
        self._route_cache.clear()

        logger.info(
            f"Registered route '{config.name}' with strategy {config.strategy} "
            f"and {len(config.target_services)} target service(s)"
        )

    def unregister_route(self, name: str) -> bool:
        """
        Unregister a route by name.

        Args:
            name: Name of the route to unregister

        Returns:
            bool: True if route was found and removed, False otherwise
        """
        initial_count = len(self._routes)
        self._routes = [r for r in self._routes if r.config.name != name]
        self._route_cache.clear()

        removed = len(self._routes) < initial_count
        if removed:
            logger.info(f"Unregistered route '{name}'")
        else:
            logger.warning(f"Route '{name}' not found for unregistration")

        return removed

    def get_route(self, name: str) -> RouteConfig | None:
        """
        Get route configuration by name.

        Args:
            name: Name of the route

        Returns:
            RouteConfig: Route configuration if found, None otherwise
        """
        for rule in self._routes:
            if rule.config.name == name:
                return rule.config
        return None

    def list_routes(self) -> list[RouteConfig]:
        """
        List all registered routes.

        Returns:
            list[RouteConfig]: List of all route configurations
        """
        return [rule.config for rule in self._routes]

    async def route_request(self, request: Request) -> str | None:
        """
        Route a request to appropriate service based on registered rules.

        Args:
            request: FastAPI request object

        Returns:
            Optional[str]: Target service URL if route found, None otherwise
        """
        # Check cache first
        cache_key = self._get_cache_key(request)
        if cache_key in self._route_cache:
            rule = self._route_cache[cache_key]
            if rule.config.enabled:
                return self._select_service(rule, request)

                # Find matching route
        for rule in self._routes:
            if not rule.config.enabled:
                continue

            try:
                if rule.matcher(request):
                    # Cache the match
                    self._route_cache[cache_key] = rule
                    return self._select_service(rule, request)
            except Exception as e:
                logger.error(
                    f"Error matching route '{rule.config.name}': {e}",
                    exc_info=True,
                )
                continue

        logger.debug(f"No route found for {request.method} {request.url.path}")
        return None

    def record_success(self, route_name: str, service_url: str) -> None:
        """
        Record successful request for a service.

        Args:
            route_name: Name of the route
            service_url: URL of the service
        """
        rule = self._find_rule(route_name)
        if rule and service_url in rule.failure_counts:
            rule.failure_counts[service_url] = 0
            rule.circuit_open[service_url] = False

    def record_failure(self, route_name: str, service_url: str) -> None:
        """
        Record failed request for a service.

        Args:
            route_name: Name of the route
            service_url: URL of the service
        """
        rule = self._find_rule(route_name)
        if rule and service_url in rule.failure_counts:
            rule.failure_counts[service_url] += 1

            # Check circuit breaker threshold
            if (
                rule.failure_counts[service_url]
                >= rule.config.circuit_breaker_threshold
            ):
                rule.circuit_open[service_url] = True
                logger.warning(
                    f"Circuit breaker opened for service {service_url} "
                    f"in route '{route_name}' after "
                    f"{rule.failure_counts[service_url]} failures"
                )

    def _create_matcher(self, config: RouteConfig) -> Callable[[Request], bool]:
        """
        Create a matcher function based on routing strategy.

        Args:
            config: Route configuration

        Returns:
            Callable: Matcher function

        Raises:
            ValueError: If routing strategy is not supported
        """
        if config.strategy == RoutingStrategy.PATH_PREFIX:
            return lambda req: req.url.path.startswith(config.pattern)

        elif config.strategy == RoutingStrategy.REGEX:
            pattern = re.compile(config.pattern)
            return lambda req: bool(pattern.match(req.url.path))

        elif config.strategy == RoutingStrategy.HEADER:
            return lambda req: all(
                req.headers.get(key) == value for key, value in config.headers.items()
            )

        elif config.strategy == RoutingStrategy.METHOD:
            methods = {m.upper() for m in config.methods}
            return lambda req: req.method.upper() in methods

        elif config.strategy == RoutingStrategy.COMPOSITE:
            # Combine multiple strategies
            matchers = []

            # Path prefix
            if config.pattern:
                matchers.append(lambda req: req.url.path.startswith(config.pattern))

                # Headers
            if config.headers:
                matchers.append(
                    lambda req: all(
                        req.headers.get(key) == value
                        for key, value in config.headers.items()
                    )
                )

                # Methods
            if config.methods:
                methods = {m.upper() for m in config.methods}
                matchers.append(lambda req: req.method.upper() in methods)

            return lambda req: all(m(req) for m in matchers)

        else:
            raise ValueError(f"Unsupported routing strategy: {config.strategy}")

    def _select_service(self, rule: RouteRule, request: Request) -> str | None:
        """
        Select target service based on load balancing strategy.

        Args:
            rule: Route rule
            request: FastAPI request object

        Returns:
            Optional[str]: Selected service URL
        """
        available_services = [
            s
            for s in rule.config.target_services
            if not rule.circuit_open.get(s, False)
        ]

        if not available_services:
            logger.error(
                f"No available services for route '{rule.config.name}' "
                f"(all circuit breakers open)"
            )
            return None

        strategy = rule.config.load_balancing

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            service = available_services[rule.current_index % len(available_services)]
            rule.current_index += 1
            return service

        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            # Select service with fewest connections
            service = min(
                available_services,
                key=lambda s: rule.connection_counts.get(s, 0),
            )
            return service

        elif strategy == LoadBalancingStrategy.RANDOM:
            import random

            return random.choice(available_services)

        elif strategy == LoadBalancingStrategy.IP_HASH:
            # Hash client IP to select service
            client_ip = request.client.host if request.client else "unknown"
            index = hash(client_ip) % len(available_services)
            return available_services[index]

        elif strategy == LoadBalancingStrategy.WEIGHTED:
            # For weighted, use round-robin (would need weights in config)
            service = available_services[rule.current_index % len(available_services)]
            rule.current_index += 1
            return service

        else:
            # Default to round-robin
            service = available_services[rule.current_index % len(available_services)]
            rule.current_index += 1
            return service

    def _find_rule(self, route_name: str) -> RouteRule | None:
        """
        Find route rule by name.

        Args:
            route_name: Name of the route

        Returns:
            Optional[RouteRule]: Route rule if found
        """
        for rule in self._routes:
            if rule.config.name == route_name:
                return rule
        return None

    def _get_cache_key(self, request: Request) -> str:
        """
        Generate cache key for request.

        Args:
            request: FastAPI request object

        Returns:
            str: Cache key
        """
        return f"{request.method}:{request.url.path}"
