"""
Service mesh support utilities for distributed services.

Provides comprehensive service mesh functionality including:
- Service registration and discovery
- Sidecar proxy configuration helpers
- mTLS configuration utilities
- Traffic splitting and routing rules
- Service health reporting
- Retry and timeout policies
- Circuit breaker integration
- Observability headers propagation

This module enables the Residency Scheduler to integrate with service mesh
platforms like Istio, Linkerd, Consul Connect, or AWS App Mesh.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies for service mesh."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    CONSISTENT_HASH = "consistent_hash"
    LOCALITY_AWARE = "locality_aware"


class HealthStatus(str, Enum):
    """Health status for service endpoints."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class TrafficProtocol(str, Enum):
    """Traffic protocols supported by service mesh."""

    HTTP = "http"
    HTTPS = "https"
    HTTP2 = "http2"
    GRPC = "grpc"
    TCP = "tcp"
    UDP = "udp"


class MTLSMode(str, Enum):
    """mTLS modes for service communication."""

    STRICT = "strict"  # Require mTLS for all traffic
    PERMISSIVE = "permissive"  # Accept both mTLS and plaintext
    DISABLED = "disabled"  # No mTLS


# ============================================================================
# Pydantic Models (Configuration)
# ============================================================================


class ServiceEndpoint(BaseModel):
    """Service endpoint configuration."""

    host: str = Field(..., description="Host address")
    port: int = Field(..., description="Port number", ge=1, le=65535)
    protocol: TrafficProtocol = Field(
        default=TrafficProtocol.HTTP,
        description="Protocol type",
    )
    weight: int = Field(
        default=100,
        description="Traffic weight for load balancing",
        ge=0,
        le=100,
    )
    health_status: HealthStatus = Field(
        default=HealthStatus.UNKNOWN,
        description="Current health status",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional endpoint metadata",
    )

    @property
    def address(self) -> str:
        """Get full endpoint address."""
        return f"{self.host}:{self.port}"

    class Config:
        use_enum_values = True


class RetryPolicy(BaseModel):
    """Retry policy configuration."""

    max_attempts: int = Field(
        default=3,
        description="Maximum retry attempts",
        ge=1,
        le=10,
    )
    per_try_timeout_ms: int = Field(
        default=2000,
        description="Timeout per retry attempt in milliseconds",
        ge=100,
    )
    retry_on: list[str] = Field(
        default_factory=lambda: ["5xx", "reset", "connect-failure", "refused-stream"],
        description="Conditions to trigger retry",
    )
    backoff_base_interval_ms: int = Field(
        default=100,
        description="Base interval for exponential backoff in milliseconds",
        ge=10,
    )
    backoff_max_interval_ms: int = Field(
        default=10000,
        description="Maximum backoff interval in milliseconds",
        ge=100,
    )
    retriable_status_codes: list[int] = Field(
        default_factory=lambda: [502, 503, 504],
        description="HTTP status codes that trigger retry",
    )

    class Config:
        use_enum_values = True


class TimeoutPolicy(BaseModel):
    """Timeout policy configuration."""

    request_timeout_ms: int = Field(
        default=30000,
        description="Total request timeout in milliseconds",
        ge=100,
    )
    idle_timeout_ms: int = Field(
        default=300000,
        description="Idle timeout for connections in milliseconds",
        ge=1000,
    )
    connect_timeout_ms: int = Field(
        default=5000,
        description="Connection timeout in milliseconds",
        ge=100,
    )

    class Config:
        use_enum_values = True


class CircuitBreakerPolicy(BaseModel):
    """Circuit breaker policy configuration."""

    consecutive_errors: int = Field(
        default=5,
        description="Consecutive errors before opening circuit",
        ge=1,
    )
    interval_ms: int = Field(
        default=10000,
        description="Detection interval in milliseconds",
        ge=1000,
    )
    base_ejection_time_ms: int = Field(
        default=30000,
        description="Base ejection time in milliseconds",
        ge=1000,
    )
    max_ejection_percent: int = Field(
        default=50,
        description="Maximum percentage of endpoints to eject",
        ge=0,
        le=100,
    )
    success_rate_minimum_hosts: int = Field(
        default=5,
        description="Minimum hosts for success rate calculation",
        ge=1,
    )
    success_rate_request_volume: int = Field(
        default=100,
        description="Minimum request volume for success rate calculation",
        ge=1,
    )
    success_rate_stdev_factor: int = Field(
        default=1900,
        description="Success rate standard deviation factor (1/1000ths)",
        ge=0,
    )

    class Config:
        use_enum_values = True


class MTLSConfig(BaseModel):
    """Mutual TLS configuration."""

    mode: MTLSMode = Field(
        default=MTLSMode.PERMISSIVE,
        description="mTLS mode",
    )
    cert_path: str = Field(
        default="",
        description="Path to TLS certificate",
    )
    key_path: str = Field(
        default="",
        description="Path to TLS private key",
    )
    ca_cert_path: str = Field(
        default="",
        description="Path to CA certificate",
    )
    client_cert_path: str = Field(
        default="",
        description="Path to client certificate for outbound connections",
    )
    client_key_path: str = Field(
        default="",
        description="Path to client private key",
    )
    verify_peer: bool = Field(
        default=True,
        description="Verify peer certificate",
    )
    min_tls_version: str = Field(
        default="1.2",
        description="Minimum TLS version",
    )
    cipher_suites: list[str] = Field(
        default_factory=list,
        description="Allowed cipher suites",
    )

    def is_enabled(self) -> bool:
        """Check if mTLS is enabled."""
        return self.mode != MTLSMode.DISABLED

    def validate_paths(self) -> bool:
        """
        Validate that required certificate paths are set.

        Returns:
            bool: True if all required paths are set
        """
        if self.mode == MTLSMode.DISABLED:
            return True

        if self.mode == MTLSMode.STRICT:
            return bool(
                self.cert_path
                and self.key_path
                and self.ca_cert_path
                and self.client_cert_path
                and self.client_key_path
            )

        # Permissive mode
        return bool(self.cert_path and self.key_path)

    class Config:
        use_enum_values = True


class TrafficWeight(BaseModel):
    """Traffic weight for a service version."""

    service_version: str = Field(..., description="Service version identifier")
    weight: int = Field(..., description="Traffic weight percentage", ge=0, le=100)
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Header-based routing conditions",
    )

    class Config:
        use_enum_values = True


class RoutingRule(BaseModel):
    """Traffic routing rule."""

    name: str = Field(..., description="Rule name")
    match_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Headers to match for this rule",
    )
    match_uri_prefix: str = Field(
        default="",
        description="URI prefix to match",
    )
    match_uri_regex: str = Field(
        default="",
        description="URI regex to match",
    )
    destination: str = Field(..., description="Destination service")
    destination_subset: str = Field(
        default="",
        description="Destination subset/version",
    )
    weight: int = Field(
        default=100,
        description="Routing weight",
        ge=0,
        le=100,
    )
    priority: int = Field(
        default=0,
        description="Rule priority (higher = evaluated first)",
        ge=0,
    )
    timeout_ms: int = Field(
        default=30000,
        description="Request timeout in milliseconds",
        ge=100,
    )
    retry_policy: RetryPolicy | None = Field(
        default=None,
        description="Retry policy for this route",
    )

    class Config:
        use_enum_values = True


class HealthCheckConfig(BaseModel):
    """Health check configuration."""

    enabled: bool = Field(default=True, description="Enable health checks")
    interval_ms: int = Field(
        default=10000,
        description="Health check interval in milliseconds",
        ge=1000,
    )
    timeout_ms: int = Field(
        default=5000,
        description="Health check timeout in milliseconds",
        ge=100,
    )
    unhealthy_threshold: int = Field(
        default=3,
        description="Consecutive failures before marking unhealthy",
        ge=1,
    )
    healthy_threshold: int = Field(
        default=2,
        description="Consecutive successes before marking healthy",
        ge=1,
    )
    path: str = Field(
        default="/health",
        description="Health check endpoint path",
    )
    expected_status_codes: list[int] = Field(
        default_factory=lambda: [200],
        description="Expected HTTP status codes for healthy",
    )

    class Config:
        use_enum_values = True


class SidecarConfig(BaseModel):
    """Sidecar proxy configuration."""

    service_name: str = Field(..., description="Service name")
    service_version: str = Field(default="v1", description="Service version")
    namespace: str = Field(default="default", description="Service namespace")
    protocol: TrafficProtocol = Field(
        default=TrafficProtocol.HTTP,
        description="Service protocol",
    )
    port: int = Field(..., description="Service port", ge=1, le=65535)
    admin_port: int = Field(
        default=15000,
        description="Sidecar admin port",
        ge=1,
        le=65535,
    )
    metrics_port: int = Field(
        default=15020,
        description="Metrics port",
        ge=1,
        le=65535,
    )
    mtls_config: MTLSConfig = Field(
        default_factory=MTLSConfig,
        description="mTLS configuration",
    )
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Default retry policy",
    )
    timeout_policy: TimeoutPolicy = Field(
        default_factory=TimeoutPolicy,
        description="Default timeout policy",
    )
    circuit_breaker: CircuitBreakerPolicy = Field(
        default_factory=CircuitBreakerPolicy,
        description="Circuit breaker configuration",
    )
    health_check: HealthCheckConfig = Field(
        default_factory=HealthCheckConfig,
        description="Health check configuration",
    )
    load_balancing: LoadBalancingStrategy = Field(
        default=LoadBalancingStrategy.ROUND_ROBIN,
        description="Load balancing strategy",
    )
    max_connections: int = Field(
        default=1024,
        description="Maximum connections",
        ge=1,
    )
    max_requests_per_connection: int = Field(
        default=100,
        description="Maximum requests per connection",
        ge=1,
    )
    enable_tracing: bool = Field(
        default=True,
        description="Enable distributed tracing",
    )
    tracing_sampling_rate: float = Field(
        default=1.0,
        description="Tracing sampling rate",
        ge=0.0,
        le=1.0,
    )
    access_logging: bool = Field(
        default=True,
        description="Enable access logging",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional sidecar metadata",
    )

    def to_envoy_config(self) -> dict[str, Any]:
        """
        Generate Envoy sidecar configuration.

        Returns:
            dict: Envoy configuration
        """
        config = {
            "admin": {
                "access_log_path": "/dev/stdout",
                "address": {
                    "socket_address": {
                        "address": "127.0.0.1",
                        "port_value": self.admin_port,
                    }
                },
            },
            "static_resources": {
                "listeners": [
                    {
                        "name": f"{self.service_name}_listener",
                        "address": {
                            "socket_address": {
                                "address": "0.0.0.0",
                                "port_value": self.port,
                            }
                        },
                        "filter_chains": [
                            {
                                "filters": [
                                    {
                                        "name": "envoy.filters.network.http_connection_manager",
                                        "typed_config": {
                                            "@type": "type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager",
                                            "stat_prefix": "ingress_http",
                                            "route_config": {
                                                "name": "local_route",
                                                "virtual_hosts": [
                                                    {
                                                        "name": self.service_name,
                                                        "domains": ["*"],
                                                        "routes": [
                                                            {
                                                                "match": {
                                                                    "prefix": "/"
                                                                },
                                                                "route": {
                                                                    "cluster": self.service_name,
                                                                    "timeout": f"{self.timeout_policy.request_timeout_ms}ms",
                                                                },
                                                            }
                                                        ],
                                                    }
                                                ],
                                            },
                                            "http_filters": [
                                                {"name": "envoy.filters.http.router"}
                                            ],
                                        },
                                    }
                                ]
                            }
                        ],
                    }
                ],
                "clusters": [
                    {
                        "name": self.service_name,
                        "connect_timeout": f"{self.timeout_policy.connect_timeout_ms}ms",
                        "type": "STRICT_DNS",
                        "lb_policy": self._get_lb_policy(),
                        "load_assignment": {
                            "cluster_name": self.service_name,
                            "endpoints": [
                                {
                                    "lb_endpoints": [
                                        {
                                            "endpoint": {
                                                "address": {
                                                    "socket_address": {
                                                        "address": "127.0.0.1",
                                                        "port_value": self.port,
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            ],
                        },
                        "circuit_breakers": self._get_circuit_breaker_config(),
                    }
                ],
            },
        }

        # Add TLS configuration if enabled
        if self.mtls_config.is_enabled():
            config["static_resources"]["clusters"][0][
                "transport_socket"
            ] = self._get_tls_config()

        return config

    def _get_lb_policy(self) -> str:
        """Get Envoy load balancing policy."""
        mapping = {
            LoadBalancingStrategy.ROUND_ROBIN: "ROUND_ROBIN",
            LoadBalancingStrategy.LEAST_CONNECTIONS: "LEAST_REQUEST",
            LoadBalancingStrategy.RANDOM: "RANDOM",
            LoadBalancingStrategy.CONSISTENT_HASH: "RING_HASH",
        }
        return mapping.get(self.load_balancing, "ROUND_ROBIN")

    def _get_circuit_breaker_config(self) -> dict[str, Any]:
        """Get circuit breaker configuration for Envoy."""
        return {
            "thresholds": [
                {
                    "max_connections": self.max_connections,
                    "max_pending_requests": self.max_connections,
                    "max_requests": self.max_requests_per_connection,
                    "max_retries": self.retry_policy.max_attempts,
                }
            ]
        }

    def _get_tls_config(self) -> dict[str, Any]:
        """Get TLS transport socket configuration."""
        return {
            "name": "envoy.transport_sockets.tls",
            "typed_config": {
                "@type": "type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext",
                "common_tls_context": {
                    "tls_certificates": [
                        {
                            "certificate_chain": {
                                "filename": self.mtls_config.cert_path
                            },
                            "private_key": {"filename": self.mtls_config.key_path},
                        }
                    ],
                    "validation_context": {
                        "trusted_ca": {"filename": self.mtls_config.ca_cert_path}
                    },
                },
            },
        }

    class Config:
        use_enum_values = True


# ============================================================================
# Dataclasses (Runtime State)
# ============================================================================


@dataclass
class ServiceRegistration:
    """Service registration information."""

    id: UUID
    name: str
    version: str
    endpoints: list[ServiceEndpoint]
    metadata: dict[str, str] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    health_status: HealthStatus = HealthStatus.UNKNOWN
    tags: list[str] = field(default_factory=list)

    def heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()

    def is_healthy(self, timeout_seconds: int = 60) -> bool:
        """
        Check if service is healthy based on heartbeat.

        Args:
            timeout_seconds: Heartbeat timeout in seconds

        Returns:
            bool: True if healthy
        """
        if self.health_status == HealthStatus.UNHEALTHY:
            return False

        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed < timeout_seconds

    def get_healthy_endpoints(self) -> list[ServiceEndpoint]:
        """Get list of healthy endpoints."""
        return [e for e in self.endpoints if e.health_status == HealthStatus.HEALTHY]


@dataclass
class TrafficSplit:
    """Traffic split configuration for A/B testing or canary deployments."""

    id: UUID
    name: str
    service_name: str
    weights: list[TrafficWeight]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    def __post_init__(self):
        """Validate weights sum to 100."""
        total = sum(w.weight for w in self.weights)
        if total != 100:
            raise ValueError(f"Traffic weights must sum to 100, got {total}")

    def is_active(self) -> bool:
        """Check if traffic split is still active."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at

    def get_destination_for_request(self, headers: dict[str, str]) -> str | None:
        """
        Determine destination version based on headers.

        Args:
            headers: Request headers

        Returns:
            str: Service version or None
        """
        # Check header-based routing first
        for weight in self.weights:
            if weight.headers:
                match = all(headers.get(k) == v for k, v in weight.headers.items())
                if match:
                    return weight.service_version

        # Fall back to weighted random selection
        import random

        rand = random.randint(1, 100)
        cumulative = 0
        for weight in self.weights:
            cumulative += weight.weight
            if rand <= cumulative:
                return weight.service_version

        return None


@dataclass
class ObservabilityHeaders:
    """Observability headers for distributed tracing."""

    request_id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    sampling_decision: bool = True
    baggage: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "ObservabilityHeaders":
        """
        Extract observability headers from request.

        Args:
            headers: Request headers

        Returns:
            ObservabilityHeaders: Extracted headers
        """
        # Support multiple tracing header formats
        trace_id = (
            headers.get("x-b3-traceid") or headers.get("traceparent", "").split("-")[1]
            if "traceparent" in headers
            else None or str(uuid4().hex)
        )

        span_id = (
            headers.get("x-b3-spanid") or headers.get("traceparent", "").split("-")[2]
            if "traceparent" in headers
            else None or str(uuid4().hex[:16])
        )

        parent_span_id = headers.get("x-b3-parentspanid")

        sampling_decision = headers.get("x-b3-sampled", "1") == "1"

        request_id = headers.get("x-request-id", str(uuid4()))

        # Parse baggage
        baggage = {}
        baggage_header = headers.get("baggage", "")
        if baggage_header:
            for item in baggage_header.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    baggage[key.strip()] = value.strip()

        return cls(
            request_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            sampling_decision=sampling_decision,
            baggage=baggage,
        )

    def to_headers(self) -> dict[str, str]:
        """
        Convert to HTTP headers.

        Returns:
            dict: Headers for propagation
        """
        headers = {
            "x-request-id": self.request_id,
            "x-b3-traceid": self.trace_id,
            "x-b3-spanid": self.span_id,
            "x-b3-sampled": "1" if self.sampling_decision else "0",
        }

        if self.parent_span_id:
            headers["x-b3-parentspanid"] = self.parent_span_id

        # W3C Trace Context format
        headers["traceparent"] = (
            f"00-{self.trace_id}-{self.span_id}-{'01' if self.sampling_decision else '00'}"
        )

        # Baggage
        if self.baggage:
            baggage_items = [f"{k}={v}" for k, v in self.baggage.items()]
            headers["baggage"] = ",".join(baggage_items)

        return headers

    def create_child_span(self) -> "ObservabilityHeaders":
        """
        Create child span for downstream calls.

        Returns:
            ObservabilityHeaders: New child span
        """
        return ObservabilityHeaders(
            request_id=self.request_id,
            trace_id=self.trace_id,
            span_id=str(uuid4().hex[:16]),
            parent_span_id=self.span_id,
            sampling_decision=self.sampling_decision,
            baggage=self.baggage.copy(),
        )


# ============================================================================
# Service Discovery
# ============================================================================


class ServiceDiscovery:
    """
    Service discovery and registration.

    Manages service registry and provides service lookup capabilities.
    """

    def __init__(self, heartbeat_timeout_seconds: int = 60):
        """
        Initialize service discovery.

        Args:
            heartbeat_timeout_seconds: Heartbeat timeout for health checks
        """
        self.services: dict[str, ServiceRegistration] = {}
        self.heartbeat_timeout = heartbeat_timeout_seconds
        self._lock = asyncio.Lock()

    async def register_service(
        self,
        name: str,
        version: str,
        endpoints: list[ServiceEndpoint],
        metadata: dict[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> ServiceRegistration:
        """
        Register a service.

        Args:
            name: Service name
            version: Service version
            endpoints: Service endpoints
            metadata: Additional metadata
            tags: Service tags

        Returns:
            ServiceRegistration: Registration record
        """
        async with self._lock:
            service_id = uuid4()
            registration = ServiceRegistration(
                id=service_id,
                name=name,
                version=version,
                endpoints=endpoints,
                metadata=metadata or {},
                tags=tags or [],
            )

            key = f"{name}:{version}"
            self.services[key] = registration

            logger.info(f"Registered service {name} version {version}")
            return registration

    async def deregister_service(self, name: str, version: str) -> bool:
        """
        Deregister a service.

        Args:
            name: Service name
            version: Service version

        Returns:
            bool: True if service was deregistered
        """
        async with self._lock:
            key = f"{name}:{version}"
            if key in self.services:
                del self.services[key]
                logger.info(f"Deregistered service {name} version {version}")
                return True
            return False

    async def heartbeat(self, name: str, version: str) -> bool:
        """
        Update service heartbeat.

        Args:
            name: Service name
            version: Service version

        Returns:
            bool: True if heartbeat was updated
        """
        async with self._lock:
            key = f"{name}:{version}"
            if key in self.services:
                self.services[key].heartbeat()
                return True
            return False

    async def discover_service(
        self,
        name: str,
        version: str | None = None,
        tags: list[str] | None = None,
    ) -> list[ServiceRegistration]:
        """
        Discover services matching criteria.

        Args:
            name: Service name
            version: Service version (optional)
            tags: Required tags (optional)

        Returns:
            list: Matching service registrations
        """
        async with self._lock:
            results = []
            for key, service in self.services.items():
                # Check name
                if service.name != name:
                    continue

                # Check version if specified
                if version and service.version != version:
                    continue

                # Check tags if specified
                if tags and not all(tag in service.tags for tag in tags):
                    continue

                # Check health
                if service.is_healthy(self.heartbeat_timeout):
                    results.append(service)

            return results

    async def get_healthy_endpoints(
        self,
        name: str,
        version: str | None = None,
    ) -> list[ServiceEndpoint]:
        """
        Get healthy endpoints for a service.

        Args:
            name: Service name
            version: Service version (optional, returns all versions if None)

        Returns:
            list: Healthy endpoints
        """
        services = await self.discover_service(name, version)
        endpoints = []
        for service in services:
            endpoints.extend(service.get_healthy_endpoints())
        return endpoints

    async def cleanup_stale_services(self) -> int:
        """
        Remove services with expired heartbeats.

        Returns:
            int: Number of services removed
        """
        async with self._lock:
            stale_keys = [
                key
                for key, service in self.services.items()
                if not service.is_healthy(self.heartbeat_timeout)
            ]

            for key in stale_keys:
                del self.services[key]
                logger.warning(f"Removed stale service: {key}")

            return len(stale_keys)

    def get_all_services(self) -> list[ServiceRegistration]:
        """
        Get all registered services.

        Returns:
            list: All service registrations
        """
        return list(self.services.values())


# ============================================================================
# Service Health Reporter
# ============================================================================


class ServiceHealthReporter:
    """
    Service health reporting for service mesh.

    Provides health check endpoints and reporting.
    """

    def __init__(self, service_name: str, version: str):
        """
        Initialize health reporter.

        Args:
            service_name: Service name
            version: Service version
        """
        self.service_name = service_name
        self.version = version
        self.health_status = HealthStatus.UNKNOWN
        self.last_check: datetime | None = None
        self.checks: dict[str, bool] = {}
        self.metadata: dict[str, Any] = {}

    def set_health_status(self, status: HealthStatus) -> None:
        """
        Set overall health status.

        Args:
            status: Health status
        """
        self.health_status = status
        self.last_check = datetime.utcnow()

    def add_health_check(self, name: str, healthy: bool) -> None:
        """
        Add individual health check result.

        Args:
            name: Check name
            healthy: Check result
        """
        self.checks[name] = healthy
        self._update_overall_status()

    def _update_overall_status(self) -> None:
        """Update overall status based on individual checks."""
        if not self.checks:
            self.health_status = HealthStatus.UNKNOWN
            return

        # All checks must pass for healthy
        if all(self.checks.values()):
            self.health_status = HealthStatus.HEALTHY
        # Some checks passing = degraded
        elif any(self.checks.values()):
            self.health_status = HealthStatus.DEGRADED
        # All checks failing = unhealthy
        else:
            self.health_status = HealthStatus.UNHEALTHY

        self.last_check = datetime.utcnow()

    def get_health_report(self) -> dict[str, Any]:
        """
        Get health report.

        Returns:
            dict: Health report
        """
        return {
            "service": self.service_name,
            "version": self.version,
            "status": self.health_status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "checks": self.checks,
            "metadata": self.metadata,
        }

    def is_healthy(self) -> bool:
        """
        Check if service is healthy.

        Returns:
            bool: True if healthy
        """
        return self.health_status == HealthStatus.HEALTHY

    def is_ready(self) -> bool:
        """
        Check if service is ready to receive traffic.

        Returns:
            bool: True if ready
        """
        return self.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


# ============================================================================
# Main Service Mesh Class
# ============================================================================


class ServiceMesh:
    """
    Main service mesh coordination class.

    Coordinates service discovery, traffic management, and observability.
    """

    def __init__(
        self,
        service_name: str,
        service_version: str = "v1",
        sidecar_config: SidecarConfig | None = None,
    ):
        """
        Initialize service mesh.

        Args:
            service_name: Service name
            service_version: Service version
            sidecar_config: Sidecar configuration
        """
        self.service_name = service_name
        self.service_version = service_version
        self.sidecar_config = sidecar_config
        self.discovery = ServiceDiscovery()
        self.health_reporter = ServiceHealthReporter(service_name, service_version)
        self.routing_rules: dict[str, RoutingRule] = {}
        self.traffic_splits: dict[str, TrafficSplit] = {}

    async def register(
        self,
        endpoints: list[ServiceEndpoint],
        metadata: dict[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> ServiceRegistration:
        """
        Register this service.

        Args:
            endpoints: Service endpoints
            metadata: Service metadata
            tags: Service tags

        Returns:
            ServiceRegistration: Registration record
        """
        return await self.discovery.register_service(
            name=self.service_name,
            version=self.service_version,
            endpoints=endpoints,
            metadata=metadata,
            tags=tags,
        )

    async def deregister(self) -> bool:
        """
        Deregister this service.

        Returns:
            bool: True if deregistered
        """
        return await self.discovery.deregister_service(
            self.service_name, self.service_version
        )

    async def heartbeat(self) -> bool:
        """
        Send heartbeat.

        Returns:
            bool: True if heartbeat sent
        """
        return await self.discovery.heartbeat(self.service_name, self.service_version)

    def add_routing_rule(self, rule: RoutingRule) -> None:
        """
        Add traffic routing rule.

        Args:
            rule: Routing rule
        """
        self.routing_rules[rule.name] = rule
        logger.info(f"Added routing rule: {rule.name}")

    def add_traffic_split(self, split: TrafficSplit) -> None:
        """
        Add traffic split configuration.

        Args:
            split: Traffic split configuration
        """
        self.traffic_splits[split.name] = split
        logger.info(f"Added traffic split: {split.name}")

    def propagate_headers(self, incoming_headers: dict[str, str]) -> dict[str, str]:
        """
        Propagate observability headers for distributed tracing.

        Args:
            incoming_headers: Incoming request headers

        Returns:
            dict: Headers to propagate to downstream services
        """
        obs_headers = ObservabilityHeaders.from_headers(incoming_headers)
        child_span = obs_headers.create_child_span()
        return child_span.to_headers()

    def get_routing_destination(
        self,
        uri: str,
        headers: dict[str, str],
    ) -> tuple[str, str] | None:
        """
        Determine routing destination based on rules.

        Args:
            uri: Request URI
            headers: Request headers

        Returns:
            tuple: (destination, subset) or None
        """
        # Sort rules by priority
        sorted_rules = sorted(
            self.routing_rules.values(),
            key=lambda r: r.priority,
            reverse=True,
        )

        for rule in sorted_rules:
            # Check URI match
            uri_match = False
            if rule.match_uri_prefix and uri.startswith(rule.match_uri_prefix):
                uri_match = True
            elif rule.match_uri_regex:
                import re

                if re.match(rule.match_uri_regex, uri):
                    uri_match = True
            elif not rule.match_uri_prefix and not rule.match_uri_regex:
                uri_match = True

            if not uri_match:
                continue

            # Check header match
            if rule.match_headers:
                headers_match = all(
                    headers.get(k) == v for k, v in rule.match_headers.items()
                )
                if not headers_match:
                    continue

            # Rule matched
            return (rule.destination, rule.destination_subset)

        return None

    def get_stats(self) -> dict[str, Any]:
        """
        Get service mesh statistics.

        Returns:
            dict: Statistics
        """
        return {
            "service": self.service_name,
            "version": self.service_version,
            "registered_services": len(self.discovery.services),
            "routing_rules": len(self.routing_rules),
            "traffic_splits": len(self.traffic_splits),
            "health": self.health_reporter.get_health_report(),
        }
