"""
Load balancing strategies for distributing traffic across service instances.

Provides:
- Round-robin load balancing
- Weighted round-robin load balancing
- Least connections load balancing
- Health-based routing
- Custom strategy support
"""

import logging
import random
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from app.loadbalancer.registry import ServiceInstance

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(ABC):
    """Abstract base class for load balancing strategies."""

    @abstractmethod
    async def select_instance(
        self,
        instances: list[ServiceInstance],
    ) -> ServiceInstance | None:
        """
        Select an instance from the available instances.

        Args:
            instances: List of available service instances

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset strategy state."""
        pass

    def get_stats(self) -> dict[str, Any]:
        """
        Get strategy statistics.

        Returns:
            Dictionary with strategy statistics
        """
        return {"strategy": self.__class__.__name__}


class RoundRobinStrategy(LoadBalancingStrategy):
    """
    Round-robin load balancing strategy.

    Distributes requests evenly across all available instances
    in a circular order.
    """

    def __init__(self) -> None:
        """Initialize round-robin strategy."""
        # Track current index per service
        self._current_index: dict[str, int] = defaultdict(int)
        self._total_selections = 0

    async def select_instance(
        self,
        instances: list[ServiceInstance],
    ) -> ServiceInstance | None:
        """
        Select instance using round-robin.

        Args:
            instances: List of available service instances

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        if not instances:
            return None

            # Get service name from first instance
        service_name = instances[0].service_name

        # Select instance at current index
        index = self._current_index[service_name] % len(instances)
        selected = instances[index]

        # Increment index for next selection
        self._current_index[service_name] = (index + 1) % len(instances)
        self._total_selections += 1

        logger.debug(
            f"Round-robin selected: {selected.endpoint} "
            f"(index: {index}/{len(instances)})"
        )

        return selected

    def reset(self) -> None:
        """Reset round-robin state."""
        self._current_index.clear()
        self._total_selections = 0

    def get_stats(self) -> dict[str, Any]:
        """Get strategy statistics."""
        return {
            "strategy": "RoundRobin",
            "total_selections": self._total_selections,
            "services_tracked": len(self._current_index),
        }


class WeightedRoundRobinStrategy(LoadBalancingStrategy):
    """
    Weighted round-robin load balancing strategy.

    Distributes requests based on instance weights. Instances with
    higher weights receive proportionally more requests.
    """

    def __init__(self) -> None:
        """Initialize weighted round-robin strategy."""
        self._current_index: dict[str, int] = defaultdict(int)
        self._current_weight: dict[str, int] = defaultdict(int)
        self._total_selections = 0

    async def select_instance(
        self,
        instances: list[ServiceInstance],
    ) -> ServiceInstance | None:
        """
        Select instance using weighted round-robin.

        Args:
            instances: List of available service instances

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        if not instances:
            return None

            # Get service name
        service_name = instances[0].service_name

        # Calculate max weight
        max_weight = max(i.weight for i in instances)
        total_weight = sum(i.weight for i in instances)

        if total_weight == 0:
            # All weights are 0, fall back to simple round-robin
            index = self._current_index[service_name] % len(instances)
            selected = instances[index]
            self._current_index[service_name] = (index + 1) % len(instances)
            self._total_selections += 1
            return selected

            # Weighted selection using smooth weighted round-robin algorithm
        while True:
            # Increment index
            index = self._current_index[service_name] % len(instances)
            instance = instances[index]

            # Increment current weight
            self._current_weight[service_name] += max_weight

            # Check if current instance should be selected
            if self._current_weight[service_name] >= instance.weight:
                self._current_weight[service_name] -= total_weight
                self._current_index[service_name] = (index + 1) % len(instances)
                self._total_selections += 1

                logger.debug(
                    f"Weighted round-robin selected: {instance.endpoint} "
                    f"(weight: {instance.weight}, index: {index}/{len(instances)})"
                )

                return instance

                # Move to next instance
            self._current_index[service_name] = (index + 1) % len(instances)

            # Safety check to prevent infinite loop
            if self._current_index[service_name] == 0:
                break

                # Fallback: select first instance
        self._total_selections += 1
        return instances[0]

    def reset(self) -> None:
        """Reset weighted round-robin state."""
        self._current_index.clear()
        self._current_weight.clear()
        self._total_selections = 0

    def get_stats(self) -> dict[str, Any]:
        """Get strategy statistics."""
        return {
            "strategy": "WeightedRoundRobin",
            "total_selections": self._total_selections,
            "services_tracked": len(self._current_index),
        }


class LeastConnectionsStrategy(LoadBalancingStrategy):
    """
    Least connections load balancing strategy.

    Routes requests to the instance with the fewest active connections.
    Useful for long-lived connections or when request processing times vary.
    """

    def __init__(self) -> None:
        """Initialize least connections strategy."""
        # Track active connections per instance
        self._connections: dict[str, int] = defaultdict(int)
        self._total_selections = 0

    async def select_instance(
        self,
        instances: list[ServiceInstance],
    ) -> ServiceInstance | None:
        """
        Select instance with least connections.

        Args:
            instances: List of available service instances

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        if not instances:
            return None

            # Find instance with minimum connections
        min_connections = float("inf")
        selected = None

        for instance in instances:
            connections = self._connections[instance.id]

            if connections < min_connections:
                min_connections = connections
                selected = instance

        if selected:
            # Increment connection count for selected instance
            self._connections[selected.id] += 1
            self._total_selections += 1

            logger.debug(
                f"Least connections selected: {selected.endpoint} "
                f"(connections: {min_connections})"
            )

        return selected

    def release_connection(self, instance_id: str) -> None:
        """
        Release a connection for an instance.

        Should be called when a connection/request is completed.

        Args:
            instance_id: ID of the instance
        """
        if instance_id in self._connections:
            self._connections[instance_id] = max(
                0,
                self._connections[instance_id] - 1,
            )

    def get_connection_count(self, instance_id: str) -> int:
        """
        Get active connection count for an instance.

        Args:
            instance_id: ID of the instance

        Returns:
            Number of active connections
        """
        return self._connections[instance_id]

    def reset(self) -> None:
        """Reset least connections state."""
        self._connections.clear()
        self._total_selections = 0

    def get_stats(self) -> dict[str, Any]:
        """Get strategy statistics."""
        total_connections = sum(self._connections.values())

        return {
            "strategy": "LeastConnections",
            "total_selections": self._total_selections,
            "active_connections": total_connections,
            "tracked_instances": len(self._connections),
        }


class HealthBasedStrategy(LoadBalancingStrategy):
    """
    Health-based load balancing strategy.

    Combines health status with another strategy. Filters out unhealthy
    instances before applying the underlying strategy.
    """

    def __init__(
        self, underlying_strategy: LoadBalancingStrategy | None = None
    ) -> None:
        """
        Initialize health-based strategy.

        Args:
            underlying_strategy: Strategy to use after filtering healthy instances
                                (defaults to RoundRobinStrategy)
        """
        self.underlying_strategy = underlying_strategy or RoundRobinStrategy()
        self._total_selections = 0
        self._unhealthy_filtered = 0

    async def select_instance(
        self,
        instances: list[ServiceInstance],
    ) -> ServiceInstance | None:
        """
        Select instance from healthy instances only.

        Args:
            instances: List of available service instances

        Returns:
            Selected ServiceInstance or None if no healthy instances available
        """
        if not instances:
            return None

            # Filter to healthy instances only
        healthy_instances = [i for i in instances if i.healthy]

        if not healthy_instances:
            self._unhealthy_filtered += len(instances)
            logger.warning(
                f"No healthy instances available for service "
                f"{instances[0].service_name}"
            )
            return None

            # Track filtered count
        self._unhealthy_filtered += len(instances) - len(healthy_instances)

        # Use underlying strategy to select from healthy instances
        selected = await self.underlying_strategy.select_instance(healthy_instances)
        self._total_selections += 1

        if selected:
            logger.debug(
                f"Health-based selected: {selected.endpoint} "
                f"(healthy: {len(healthy_instances)}/{len(instances)})"
            )

        return selected

    def reset(self) -> None:
        """Reset health-based strategy state."""
        self.underlying_strategy.reset()
        self._total_selections = 0
        self._unhealthy_filtered = 0

    def get_stats(self) -> dict[str, Any]:
        """Get strategy statistics."""
        underlying_stats = self.underlying_strategy.get_stats()

        return {
            "strategy": "HealthBased",
            "underlying_strategy": underlying_stats.get("strategy"),
            "total_selections": self._total_selections,
            "unhealthy_filtered": self._unhealthy_filtered,
            "underlying_stats": underlying_stats,
        }


class RandomStrategy(LoadBalancingStrategy):
    """
    Random load balancing strategy.

    Selects a random instance from available instances.
    """

    def __init__(self) -> None:
        """Initialize random strategy."""
        self._total_selections = 0

    async def select_instance(
        self,
        instances: list[ServiceInstance],
    ) -> ServiceInstance | None:
        """
        Select random instance.

        Args:
            instances: List of available service instances

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        if not instances:
            return None

        selected = random.choice(instances)
        self._total_selections += 1

        logger.debug(f"Random selected: {selected.endpoint}")

        return selected

    def reset(self) -> None:
        """Reset random strategy state."""
        self._total_selections = 0

    def get_stats(self) -> dict[str, Any]:
        """Get strategy statistics."""
        return {
            "strategy": "Random",
            "total_selections": self._total_selections,
        }


class IPHashStrategy(LoadBalancingStrategy):
    """
    IP hash load balancing strategy.

    Routes requests from the same client IP to the same instance.
    Useful for maintaining session affinity.
    """

    def __init__(self) -> None:
        """Initialize IP hash strategy."""
        self._total_selections = 0
        self._cache: dict[str, str] = {}  # Maps client_ip -> instance_id

    async def select_instance(
        self,
        instances: list[ServiceInstance],
        client_ip: str | None = None,
    ) -> ServiceInstance | None:
        """
        Select instance based on client IP hash.

        Args:
            instances: List of available service instances
            client_ip: Client IP address

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        if not instances:
            return None

        if not client_ip:
            # No client IP provided, fall back to random
            selected = random.choice(instances)
            self._total_selections += 1
            return selected

            # Check cache first
        if client_ip in self._cache:
            cached_id = self._cache[client_ip]
            for instance in instances:
                if instance.id == cached_id:
                    logger.debug(
                        f"IP hash (cached) selected: {instance.endpoint} "
                        f"for {client_ip}"
                    )
                    self._total_selections += 1
                    return instance

                    # Calculate hash and select instance
        hash_value = hash(client_ip)
        index = hash_value % len(instances)
        selected = instances[index]

        # Cache the selection
        self._cache[client_ip] = selected.id

        logger.debug(
            f"IP hash selected: {selected.endpoint} for {client_ip} "
            f"(hash: {hash_value}, index: {index})"
        )

        self._total_selections += 1
        return selected

    def reset(self) -> None:
        """Reset IP hash strategy state."""
        self._total_selections = 0
        self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get strategy statistics."""
        return {
            "strategy": "IPHash",
            "total_selections": self._total_selections,
            "cached_mappings": len(self._cache),
        }
