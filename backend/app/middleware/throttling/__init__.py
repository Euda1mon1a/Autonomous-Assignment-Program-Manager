"""
Request throttling middleware package.

Provides comprehensive request throttling with concurrent request limiting,
queue management, priority-based throttling, and graceful degradation.

Usage:
    from app.middleware.throttling import ThrottlingMiddleware

    app.add_middleware(ThrottlingMiddleware, strategy="adaptive")

Components:
    - ThrottlingMiddleware: Main middleware for request throttling
    - ThrottleStorage: Redis-based storage for throttling state
    - ThrottleStrategy: Base class for throttling strategies
    - ThrottleConfig: Configuration classes for throttling
    - ThrottlePriority: Request priority levels

Strategies:
    - SimpleThrottleStrategy: Basic allow/reject throttling
    - QueuedThrottleStrategy: Throttling with request queuing
    - PriorityThrottleStrategy: Priority-based throttling
    - AdaptiveThrottleStrategy: Adaptive throttling with graceful degradation

Features:
    - Concurrent request limiting (max N requests at a time)
    - Request queue management with priority ordering
    - Priority-based throttling (critical > high > normal > low > background)
    - Endpoint-specific limits (e.g., /schedules/generate limited to 5 concurrent)
    - User-based throttling (different limits per user role)
    - Graceful degradation (adaptive behavior under load)
    - Backpressure handling (reject low priority when under stress)
    - Real-time metrics (active requests, queue depth, utilization)
"""

from app.middleware.throttling.config import (
    DEFAULT_THROTTLE_CONFIG,
    DEGRADATION_THRESHOLDS,
    ENDPOINT_THROTTLE_CONFIGS,
    ROLE_THROTTLE_LIMITS,
    EndpointThrottleConfig,
    ThrottleConfig,
    ThrottlePriority,
    UserThrottleConfig,
    get_endpoint_config,
    get_priority_for_endpoint,
    get_role_config,
)
from app.middleware.throttling.middleware import ThrottlingMiddleware
from app.middleware.throttling.storage import (
    QueuedRequest,
    RequestSlot,
    ThrottleMetrics,
    ThrottleStorage,
)
from app.middleware.throttling.strategies import (
    AdaptiveThrottleStrategy,
    PriorityThrottleStrategy,
    QueuedThrottleStrategy,
    SimpleThrottleStrategy,
    ThrottleAction,
    ThrottleDecision,
    ThrottleStrategy,
    create_throttle_response,
)

__all__ = [
    # Main middleware
    "ThrottlingMiddleware",
    # Configuration
    "ThrottleConfig",
    "EndpointThrottleConfig",
    "UserThrottleConfig",
    "ThrottlePriority",
    "DEFAULT_THROTTLE_CONFIG",
    "ENDPOINT_THROTTLE_CONFIGS",
    "ROLE_THROTTLE_LIMITS",
    "DEGRADATION_THRESHOLDS",
    "get_endpoint_config",
    "get_role_config",
    "get_priority_for_endpoint",
    # Storage
    "ThrottleStorage",
    "RequestSlot",
    "QueuedRequest",
    "ThrottleMetrics",
    # Strategies
    "ThrottleStrategy",
    "SimpleThrottleStrategy",
    "QueuedThrottleStrategy",
    "PriorityThrottleStrategy",
    "AdaptiveThrottleStrategy",
    "ThrottleAction",
    "ThrottleDecision",
    "create_throttle_response",
]
