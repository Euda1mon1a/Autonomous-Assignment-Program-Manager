"""
Configuration for request throttling middleware.

Defines throttling limits, priorities, and endpoint-specific configurations.
"""

from dataclasses import dataclass
from enum import Enum


class ThrottlePriority(str, Enum):
    """Request priority levels for throttling."""

    CRITICAL = "critical"  # Emergency operations, health checks
    HIGH = "high"  # Important user operations
    NORMAL = "normal"  # Standard requests
    LOW = "low"  # Background tasks, analytics
    BACKGROUND = "background"  # Batch operations, reports


@dataclass
class ThrottleConfig:
    """Configuration for throttling limits."""

    max_concurrent_requests: int  # Maximum concurrent requests
    max_queue_size: int  # Maximum queue size before rejection
    queue_timeout_seconds: float  # Timeout for queued requests
    enabled: bool = True  # Enable/disable throttling


@dataclass
class EndpointThrottleConfig:
    """Per-endpoint throttling configuration."""

    endpoint_pattern: str  # Endpoint pattern (e.g., "/api/schedules/*")
    max_concurrent: int  # Max concurrent requests for this endpoint
    max_queue_size: int  # Max queue size for this endpoint
    queue_timeout: float  # Queue timeout in seconds
    priority: ThrottlePriority = ThrottlePriority.NORMAL  # Default priority


@dataclass
class UserThrottleConfig:
    """Per-user throttling configuration."""

    user_id: str  # User identifier
    max_concurrent: int  # Max concurrent requests for this user
    max_queue_size: int  # Max queue size for this user
    queue_timeout: float  # Queue timeout in seconds
    priority_boost: bool = False  # Whether to boost priority


# Default global throttling configuration
DEFAULT_THROTTLE_CONFIG = ThrottleConfig(
    max_concurrent_requests=100,  # 100 concurrent requests globally
    max_queue_size=200,  # 200 queued requests before rejection
    queue_timeout_seconds=30.0,  # 30 second timeout for queued requests
    enabled=True,
)

# Endpoint-specific throttling configurations
ENDPOINT_THROTTLE_CONFIGS = {
    # High-concurrency endpoints
    "/api/v1/health": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/health",
        max_concurrent=50,
        max_queue_size=0,  # No queuing for health checks
        queue_timeout=1.0,
        priority=ThrottlePriority.CRITICAL,
    ),
    "/api/v1/metrics": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/metrics",
        max_concurrent=20,
        max_queue_size=0,
        queue_timeout=1.0,
        priority=ThrottlePriority.CRITICAL,
    ),
    # Schedule generation (expensive operations)
    "/api/v1/schedules/generate": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/schedules/generate",
        max_concurrent=5,  # Limited due to computational cost
        max_queue_size=10,
        queue_timeout=60.0,
        priority=ThrottlePriority.HIGH,
    ),
    "/api/v1/schedules/validate": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/schedules/validate",
        max_concurrent=10,
        max_queue_size=20,
        queue_timeout=30.0,
        priority=ThrottlePriority.HIGH,
    ),
    # Swap operations
    "/api/v1/swaps/execute": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/swaps/execute",
        max_concurrent=10,
        max_queue_size=15,
        queue_timeout=20.0,
        priority=ThrottlePriority.HIGH,
    ),
    # Analytics and reporting (lower priority)
    "/api/v1/analytics/*": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/analytics/*",
        max_concurrent=15,
        max_queue_size=30,
        queue_timeout=45.0,
        priority=ThrottlePriority.LOW,
    ),
    "/api/v1/reports/*": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/reports/*",
        max_concurrent=10,
        max_queue_size=20,
        queue_timeout=60.0,
        priority=ThrottlePriority.BACKGROUND,
    ),
    # Standard CRUD operations
    "/api/v1/persons/*": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/persons/*",
        max_concurrent=30,
        max_queue_size=50,
        queue_timeout=15.0,
        priority=ThrottlePriority.NORMAL,
    ),
    "/api/v1/assignments/*": EndpointThrottleConfig(
        endpoint_pattern="/api/v1/assignments/*",
        max_concurrent=25,
        max_queue_size=40,
        queue_timeout=15.0,
        priority=ThrottlePriority.NORMAL,
    ),
}

# Role-based default throttling
ROLE_THROTTLE_LIMITS = {
    "ADMIN": ThrottleConfig(
        max_concurrent_requests=50,
        max_queue_size=100,
        queue_timeout_seconds=45.0,
    ),
    "COORDINATOR": ThrottleConfig(
        max_concurrent_requests=30,
        max_queue_size=60,
        queue_timeout_seconds=30.0,
    ),
    "FACULTY": ThrottleConfig(
        max_concurrent_requests=20,
        max_queue_size=40,
        queue_timeout_seconds=30.0,
    ),
    "RESIDENT": ThrottleConfig(
        max_concurrent_requests=15,
        max_queue_size=30,
        queue_timeout_seconds=20.0,
    ),
    "CLINICAL_STAFF": ThrottleConfig(
        max_concurrent_requests=15,
        max_queue_size=30,
        queue_timeout_seconds=20.0,
    ),
    "RN": ThrottleConfig(
        max_concurrent_requests=10,
        max_queue_size=20,
        queue_timeout_seconds=15.0,
    ),
    "LPN": ThrottleConfig(
        max_concurrent_requests=10,
        max_queue_size=20,
        queue_timeout_seconds=15.0,
    ),
    "MSA": ThrottleConfig(
        max_concurrent_requests=10,
        max_queue_size=20,
        queue_timeout_seconds=15.0,
    ),
}

# Graceful degradation thresholds
DEGRADATION_THRESHOLDS = {
    "warning": 0.70,  # 70% capacity - start warning
    "throttle": 0.80,  # 80% capacity - start aggressive throttling
    "reject": 0.90,  # 90% capacity - reject low priority requests
    "critical": 0.95,  # 95% capacity - emergency mode
}


def get_endpoint_config(endpoint: str) -> EndpointThrottleConfig | None:
    """
    Get throttling configuration for a specific endpoint.

    Args:
        endpoint: Endpoint path

    Returns:
        EndpointThrottleConfig if found, None otherwise
    """
    # Exact match first
    if endpoint in ENDPOINT_THROTTLE_CONFIGS:
        return ENDPOINT_THROTTLE_CONFIGS[endpoint]

    # Pattern matching (e.g., /api/v1/analytics/*)
    for pattern, config in ENDPOINT_THROTTLE_CONFIGS.items():
        if pattern.endswith("*"):
            prefix = pattern[:-1]  # Remove the *
            if endpoint.startswith(prefix):
                return config

    return None


def get_role_config(role: str | None) -> ThrottleConfig:
    """
    Get throttling configuration for a user role.

    Args:
        role: User role (e.g., "ADMIN", "FACULTY")

    Returns:
        ThrottleConfig for the role, or default config
    """
    if role and role in ROLE_THROTTLE_LIMITS:
        return ROLE_THROTTLE_LIMITS[role]
    return DEFAULT_THROTTLE_CONFIG


def get_priority_for_endpoint(endpoint: str) -> ThrottlePriority:
    """
    Get priority level for an endpoint.

    Args:
        endpoint: Endpoint path

    Returns:
        ThrottlePriority for the endpoint
    """
    config = get_endpoint_config(endpoint)
    if config:
        return config.priority
    return ThrottlePriority.NORMAL
