"""
Load balancing utilities for distributed service management.

Provides:
- Service registry and discovery
- Multiple load balancing strategies (round-robin, weighted, least connections)
- Health-based routing
- Failover handling
- Service instance management
- Load balancer coordination
"""

from app.loadbalancer.balancer import LoadBalancer
from app.loadbalancer.health import HealthStatus, ServiceHealthChecker
from app.loadbalancer.registry import ServiceInstance, ServiceRegistry
from app.loadbalancer.strategies import (
    HealthBasedStrategy,
    LeastConnectionsStrategy,
    LoadBalancingStrategy,
    RoundRobinStrategy,
    WeightedRoundRobinStrategy,
)

__all__ = [
    "LoadBalancer",
    "ServiceRegistry",
    "ServiceInstance",
    "ServiceHealthChecker",
    "HealthStatus",
    "LoadBalancingStrategy",
    "RoundRobinStrategy",
    "WeightedRoundRobinStrategy",
    "LeastConnectionsStrategy",
    "HealthBasedStrategy",
]
