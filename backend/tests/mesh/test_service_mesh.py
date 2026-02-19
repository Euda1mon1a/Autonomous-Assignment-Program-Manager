"""Tests for service mesh models, configs, and pure logic (no external deps)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.mesh.service_mesh import (
    CircuitBreakerPolicy,
    CircuitBreakerState,
    HealthCheckConfig,
    HealthStatus,
    LoadBalancingStrategy,
    MTLSConfig,
    MTLSMode,
    ObservabilityHeaders,
    RetryPolicy,
    RoutingRule,
    ServiceDiscovery,
    ServiceEndpoint,
    ServiceHealthReporter,
    ServiceMesh,
    ServiceRegistration,
    SidecarConfig,
    TimeoutPolicy,
    TrafficProtocol,
    TrafficSplit,
    TrafficWeight,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestLoadBalancingStrategy:
    def test_all_values(self):
        assert LoadBalancingStrategy.ROUND_ROBIN == "round_robin"
        assert LoadBalancingStrategy.LEAST_CONNECTIONS == "least_connections"
        assert LoadBalancingStrategy.RANDOM == "random"
        assert LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN == "weighted_round_robin"
        assert LoadBalancingStrategy.CONSISTENT_HASH == "consistent_hash"
        assert LoadBalancingStrategy.LOCALITY_AWARE == "locality_aware"

    def test_count(self):
        assert len(LoadBalancingStrategy) == 6

    def test_is_str_enum(self):
        assert isinstance(LoadBalancingStrategy.ROUND_ROBIN, str)


class TestHealthStatus:
    def test_all_values(self):
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"

    def test_count(self):
        assert len(HealthStatus) == 4


class TestCircuitBreakerState:
    def test_all_values(self):
        assert CircuitBreakerState.CLOSED == "closed"
        assert CircuitBreakerState.OPEN == "open"
        assert CircuitBreakerState.HALF_OPEN == "half_open"

    def test_count(self):
        assert len(CircuitBreakerState) == 3


class TestTrafficProtocol:
    def test_all_values(self):
        assert TrafficProtocol.HTTP == "http"
        assert TrafficProtocol.HTTPS == "https"
        assert TrafficProtocol.HTTP2 == "http2"
        assert TrafficProtocol.GRPC == "grpc"
        assert TrafficProtocol.TCP == "tcp"
        assert TrafficProtocol.UDP == "udp"

    def test_count(self):
        assert len(TrafficProtocol) == 6


class TestMTLSMode:
    def test_all_values(self):
        assert MTLSMode.STRICT == "strict"
        assert MTLSMode.PERMISSIVE == "permissive"
        assert MTLSMode.DISABLED == "disabled"

    def test_count(self):
        assert len(MTLSMode) == 3


# ---------------------------------------------------------------------------
# ServiceEndpoint
# ---------------------------------------------------------------------------


class TestServiceEndpoint:
    def test_creation(self):
        ep = ServiceEndpoint(host="localhost", port=8080)
        assert ep.host == "localhost"
        assert ep.port == 8080

    def test_defaults(self):
        ep = ServiceEndpoint(host="svc", port=80)
        assert ep.protocol == TrafficProtocol.HTTP
        assert ep.weight == 100
        assert ep.health_status == HealthStatus.UNKNOWN
        assert ep.metadata == {}

    def test_address_property(self):
        ep = ServiceEndpoint(host="10.0.0.1", port=443)
        assert ep.address == "10.0.0.1:443"

    def test_port_validation_low(self):
        with pytest.raises(ValidationError):
            ServiceEndpoint(host="h", port=0)

    def test_port_validation_high(self):
        with pytest.raises(ValidationError):
            ServiceEndpoint(host="h", port=70000)

    def test_weight_validation(self):
        with pytest.raises(ValidationError):
            ServiceEndpoint(host="h", port=80, weight=101)


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------


class TestRetryPolicy:
    def test_defaults(self):
        rp = RetryPolicy()
        assert rp.max_attempts == 3
        assert rp.per_try_timeout_ms == 2000
        assert rp.backoff_base_interval_ms == 100
        assert rp.backoff_max_interval_ms == 10000
        assert rp.retriable_status_codes == [502, 503, 504]

    def test_retry_on_default(self):
        rp = RetryPolicy()
        assert "5xx" in rp.retry_on
        assert "connect-failure" in rp.retry_on

    def test_max_attempts_validation(self):
        with pytest.raises(ValidationError):
            RetryPolicy(max_attempts=0)

    def test_max_attempts_upper(self):
        with pytest.raises(ValidationError):
            RetryPolicy(max_attempts=11)


# ---------------------------------------------------------------------------
# TimeoutPolicy
# ---------------------------------------------------------------------------


class TestTimeoutPolicy:
    def test_defaults(self):
        tp = TimeoutPolicy()
        assert tp.request_timeout_ms == 30000
        assert tp.idle_timeout_ms == 300000
        assert tp.connect_timeout_ms == 5000

    def test_validation(self):
        with pytest.raises(ValidationError):
            TimeoutPolicy(request_timeout_ms=50)  # ge=100


# ---------------------------------------------------------------------------
# CircuitBreakerPolicy
# ---------------------------------------------------------------------------


class TestCircuitBreakerPolicy:
    def test_defaults(self):
        cb = CircuitBreakerPolicy()
        assert cb.consecutive_errors == 5
        assert cb.interval_ms == 10000
        assert cb.base_ejection_time_ms == 30000
        assert cb.max_ejection_percent == 50

    def test_validation(self):
        with pytest.raises(ValidationError):
            CircuitBreakerPolicy(max_ejection_percent=101)


# ---------------------------------------------------------------------------
# MTLSConfig
# ---------------------------------------------------------------------------


class TestMTLSConfig:
    def test_defaults(self):
        m = MTLSConfig()
        assert m.mode == MTLSMode.PERMISSIVE
        assert m.cert_path == ""
        assert m.verify_peer is True
        assert m.min_tls_version == "1.2"

    def test_is_enabled_permissive(self):
        m = MTLSConfig(mode=MTLSMode.PERMISSIVE)
        assert m.is_enabled() is True

    def test_is_enabled_strict(self):
        m = MTLSConfig(mode=MTLSMode.STRICT)
        assert m.is_enabled() is True

    def test_is_enabled_disabled(self):
        m = MTLSConfig(mode=MTLSMode.DISABLED)
        assert m.is_enabled() is False

    def test_validate_paths_disabled(self):
        m = MTLSConfig(mode=MTLSMode.DISABLED)
        assert m.validate_paths() is True

    def test_validate_paths_strict_missing(self):
        m = MTLSConfig(mode=MTLSMode.STRICT)
        assert m.validate_paths() is False

    def test_validate_paths_strict_complete(self):
        m = MTLSConfig(
            mode=MTLSMode.STRICT,
            cert_path="/cert.pem",
            key_path="/key.pem",
            ca_cert_path="/ca.pem",
            client_cert_path="/client.pem",
            client_key_path="/client-key.pem",
        )
        assert m.validate_paths() is True

    def test_validate_paths_permissive_missing(self):
        m = MTLSConfig(mode=MTLSMode.PERMISSIVE)
        assert m.validate_paths() is False

    def test_validate_paths_permissive_with_paths(self):
        m = MTLSConfig(
            mode=MTLSMode.PERMISSIVE,
            cert_path="/cert.pem",
            key_path="/key.pem",
        )
        assert m.validate_paths() is True


# ---------------------------------------------------------------------------
# TrafficWeight / RoutingRule / HealthCheckConfig
# ---------------------------------------------------------------------------


class TestTrafficWeight:
    def test_creation(self):
        tw = TrafficWeight(service_version="v1", weight=80)
        assert tw.service_version == "v1"
        assert tw.weight == 80

    def test_weight_validation(self):
        with pytest.raises(ValidationError):
            TrafficWeight(service_version="v1", weight=-1)

    def test_headers_default(self):
        tw = TrafficWeight(service_version="v1", weight=50)
        assert tw.headers == {}


class TestRoutingRule:
    def test_creation(self):
        rr = RoutingRule(name="test-route", destination="svc-a")
        assert rr.name == "test-route"
        assert rr.destination == "svc-a"
        assert rr.weight == 100
        assert rr.priority == 0
        assert rr.timeout_ms == 30000

    def test_with_retry_policy(self):
        rp = RetryPolicy(max_attempts=5)
        rr = RoutingRule(name="r", destination="d", retry_policy=rp)
        assert rr.retry_policy.max_attempts == 5


class TestHealthCheckConfig:
    def test_defaults(self):
        hc = HealthCheckConfig()
        assert hc.enabled is True
        assert hc.interval_ms == 10000
        assert hc.timeout_ms == 5000
        assert hc.unhealthy_threshold == 3
        assert hc.healthy_threshold == 2
        assert hc.path == "/health"
        assert hc.expected_status_codes == [200]


# ---------------------------------------------------------------------------
# SidecarConfig
# ---------------------------------------------------------------------------


class TestSidecarConfig:
    def _make(self, **overrides) -> SidecarConfig:
        defaults = {"service_name": "test-svc", "port": 8080}
        defaults.update(overrides)
        return SidecarConfig(**defaults)

    def test_defaults(self):
        sc = self._make()
        assert sc.service_version == "v1"
        assert sc.namespace == "default"
        assert sc.admin_port == 15000
        assert sc.load_balancing == LoadBalancingStrategy.ROUND_ROBIN
        assert sc.max_connections == 1024
        assert sc.enable_tracing is True
        assert sc.tracing_sampling_rate == 1.0

    def test_to_envoy_config_structure(self):
        sc = self._make()
        config = sc.to_envoy_config()
        assert "admin" in config
        assert "static_resources" in config
        sr = config["static_resources"]
        assert "listeners" in sr
        assert "clusters" in sr
        assert len(sr["listeners"]) == 1
        assert len(sr["clusters"]) == 1

    def test_to_envoy_config_service_name(self):
        sc = self._make(service_name="my-svc")
        config = sc.to_envoy_config()
        cluster = config["static_resources"]["clusters"][0]
        assert cluster["name"] == "my-svc"

    def test_to_envoy_config_timeout(self):
        sc = self._make()
        config = sc.to_envoy_config()
        cluster = config["static_resources"]["clusters"][0]
        assert cluster["connect_timeout"] == "5000ms"

    def test_to_envoy_config_with_mtls(self):
        sc = self._make(
            mtls_config=MTLSConfig(
                mode=MTLSMode.STRICT,
                cert_path="/cert.pem",
                key_path="/key.pem",
                ca_cert_path="/ca.pem",
            )
        )
        config = sc.to_envoy_config()
        cluster = config["static_resources"]["clusters"][0]
        assert "transport_socket" in cluster

    def test_to_envoy_config_without_mtls(self):
        sc = self._make(mtls_config=MTLSConfig(mode=MTLSMode.DISABLED))
        config = sc.to_envoy_config()
        cluster = config["static_resources"]["clusters"][0]
        assert "transport_socket" not in cluster

    def test_get_lb_policy_round_robin(self):
        sc = self._make(load_balancing=LoadBalancingStrategy.ROUND_ROBIN)
        assert sc._get_lb_policy() == "ROUND_ROBIN"

    def test_get_lb_policy_least_connections(self):
        sc = self._make(load_balancing=LoadBalancingStrategy.LEAST_CONNECTIONS)
        assert sc._get_lb_policy() == "LEAST_REQUEST"

    def test_get_lb_policy_random(self):
        sc = self._make(load_balancing=LoadBalancingStrategy.RANDOM)
        assert sc._get_lb_policy() == "RANDOM"

    def test_get_lb_policy_consistent_hash(self):
        sc = self._make(load_balancing=LoadBalancingStrategy.CONSISTENT_HASH)
        assert sc._get_lb_policy() == "RING_HASH"

    def test_get_lb_policy_unmapped_defaults(self):
        sc = self._make(load_balancing=LoadBalancingStrategy.LOCALITY_AWARE)
        assert sc._get_lb_policy() == "ROUND_ROBIN"

    def test_get_circuit_breaker_config(self):
        sc = self._make(max_connections=512, max_requests_per_connection=50)
        cb_config = sc._get_circuit_breaker_config()
        assert cb_config["thresholds"][0]["max_connections"] == 512
        assert cb_config["thresholds"][0]["max_requests"] == 50

    def test_get_tls_config(self):
        sc = self._make(
            mtls_config=MTLSConfig(
                cert_path="/c.pem",
                key_path="/k.pem",
                ca_cert_path="/ca.pem",
            )
        )
        tls = sc._get_tls_config()
        assert tls["name"] == "envoy.transport_sockets.tls"
        tc = tls["typed_config"]["common_tls_context"]
        assert tc["tls_certificates"][0]["certificate_chain"]["filename"] == "/c.pem"
        assert tc["validation_context"]["trusted_ca"]["filename"] == "/ca.pem"


# ---------------------------------------------------------------------------
# ServiceRegistration
# ---------------------------------------------------------------------------


class TestServiceRegistration:
    def _make(self, **overrides) -> ServiceRegistration:
        defaults = {
            "id": uuid4(),
            "name": "svc",
            "version": "v1",
            "endpoints": [],
        }
        defaults.update(overrides)
        return ServiceRegistration(**defaults)

    def test_creation(self):
        sr = self._make()
        assert sr.name == "svc"
        assert sr.version == "v1"
        assert sr.health_status == HealthStatus.UNKNOWN

    def test_heartbeat(self):
        sr = self._make()
        old_hb = sr.last_heartbeat
        sr.heartbeat()
        assert sr.last_heartbeat >= old_hb

    def test_is_healthy_fresh(self):
        sr = self._make()
        assert sr.is_healthy(timeout_seconds=60) is True

    def test_is_healthy_stale(self):
        sr = self._make()
        sr.last_heartbeat = datetime.now(UTC) - timedelta(seconds=120)
        assert sr.is_healthy(timeout_seconds=60) is False

    def test_is_healthy_explicit_unhealthy(self):
        sr = self._make(health_status=HealthStatus.UNHEALTHY)
        assert sr.is_healthy(timeout_seconds=9999) is False

    def test_get_healthy_endpoints(self):
        ep_healthy = ServiceEndpoint(
            host="h1", port=80, health_status=HealthStatus.HEALTHY
        )
        ep_unhealthy = ServiceEndpoint(
            host="h2", port=80, health_status=HealthStatus.UNHEALTHY
        )
        ep_unknown = ServiceEndpoint(host="h3", port=80)
        sr = self._make(endpoints=[ep_healthy, ep_unhealthy, ep_unknown])
        healthy = sr.get_healthy_endpoints()
        assert len(healthy) == 1
        assert healthy[0].host == "h1"


# ---------------------------------------------------------------------------
# TrafficSplit
# ---------------------------------------------------------------------------


class TestTrafficSplit:
    def _weights(self, *pairs) -> list[TrafficWeight]:
        return [TrafficWeight(service_version=v, weight=w) for v, w in pairs]

    def test_valid_creation(self):
        ts = TrafficSplit(
            id=uuid4(),
            name="canary",
            service_name="svc",
            weights=self._weights(("v1", 90), ("v2", 10)),
        )
        assert ts.name == "canary"

    def test_invalid_weight_sum(self):
        with pytest.raises(ValueError, match="must sum to 100"):
            TrafficSplit(
                id=uuid4(),
                name="bad",
                service_name="svc",
                weights=self._weights(("v1", 50), ("v2", 30)),
            )

    def test_is_active_no_expiry(self):
        ts = TrafficSplit(
            id=uuid4(),
            name="t",
            service_name="s",
            weights=self._weights(("v1", 100)),
        )
        assert ts.is_active() is True

    def test_is_active_future_expiry(self):
        ts = TrafficSplit(
            id=uuid4(),
            name="t",
            service_name="s",
            weights=self._weights(("v1", 100)),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert ts.is_active() is True

    def test_is_active_expired(self):
        ts = TrafficSplit(
            id=uuid4(),
            name="t",
            service_name="s",
            weights=self._weights(("v1", 100)),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert ts.is_active() is False

    def test_get_destination_by_header(self):
        w1 = TrafficWeight(
            service_version="v2", weight=10, headers={"x-canary": "true"}
        )
        w2 = TrafficWeight(service_version="v1", weight=90)
        ts = TrafficSplit(
            id=uuid4(),
            name="canary",
            service_name="svc",
            weights=[w1, w2],
        )
        result = ts.get_destination_for_request({"x-canary": "true"})
        assert result == "v2"

    def test_get_destination_single_weight(self):
        """With only one weight of 100, random always picks it."""
        ts = TrafficSplit(
            id=uuid4(),
            name="t",
            service_name="s",
            weights=self._weights(("v1", 100)),
        )
        result = ts.get_destination_for_request({})
        assert result == "v1"


# ---------------------------------------------------------------------------
# ObservabilityHeaders
# ---------------------------------------------------------------------------


class TestObservabilityHeaders:
    def test_creation(self):
        oh = ObservabilityHeaders(
            request_id="req-1",
            trace_id="trace-1",
            span_id="span-1",
        )
        assert oh.request_id == "req-1"
        assert oh.parent_span_id is None
        assert oh.sampling_decision is True
        assert oh.baggage == {}

    def test_to_headers(self):
        oh = ObservabilityHeaders(
            request_id="r1",
            trace_id="t1",
            span_id="s1",
        )
        headers = oh.to_headers()
        assert headers["x-request-id"] == "r1"
        assert headers["x-b3-traceid"] == "t1"
        assert headers["x-b3-spanid"] == "s1"
        assert headers["x-b3-sampled"] == "1"
        assert "traceparent" in headers

    def test_to_headers_with_parent(self):
        oh = ObservabilityHeaders(
            request_id="r1",
            trace_id="t1",
            span_id="s1",
            parent_span_id="p1",
        )
        headers = oh.to_headers()
        assert headers["x-b3-parentspanid"] == "p1"

    def test_to_headers_sampling_off(self):
        oh = ObservabilityHeaders(
            request_id="r",
            trace_id="t",
            span_id="s",
            sampling_decision=False,
        )
        headers = oh.to_headers()
        assert headers["x-b3-sampled"] == "0"
        assert headers["traceparent"].endswith("-00")

    def test_to_headers_baggage(self):
        oh = ObservabilityHeaders(
            request_id="r",
            trace_id="t",
            span_id="s",
            baggage={"user": "123", "env": "prod"},
        )
        headers = oh.to_headers()
        assert "baggage" in headers
        assert "user=123" in headers["baggage"]
        assert "env=prod" in headers["baggage"]

    def test_create_child_span(self):
        parent = ObservabilityHeaders(
            request_id="r1",
            trace_id="t1",
            span_id="s1",
            baggage={"key": "val"},
        )
        child = parent.create_child_span()
        assert child.request_id == "r1"
        assert child.trace_id == "t1"
        assert child.span_id != "s1"  # new span
        assert child.parent_span_id == "s1"
        assert child.baggage == {"key": "val"}

    def test_create_child_span_baggage_isolation(self):
        parent = ObservabilityHeaders(
            request_id="r",
            trace_id="t",
            span_id="s",
            baggage={"a": "1"},
        )
        child = parent.create_child_span()
        child.baggage["b"] = "2"
        assert "b" not in parent.baggage

    def test_from_headers_b3(self):
        headers = {
            "x-b3-traceid": "abc123",
            "x-b3-spanid": "def456",
            "x-b3-parentspanid": "parent1",
            "x-b3-sampled": "1",
            "x-request-id": "req-99",
        }
        oh = ObservabilityHeaders.from_headers(headers)
        assert oh.request_id == "req-99"
        assert oh.parent_span_id == "parent1"
        assert oh.sampling_decision is True

    def test_from_headers_sampling_off(self):
        headers = {
            "x-b3-traceid": "t",
            "x-b3-spanid": "s",
            "x-b3-sampled": "0",
        }
        oh = ObservabilityHeaders.from_headers(headers)
        assert oh.sampling_decision is False

    def test_from_headers_baggage_parsing(self):
        headers = {
            "x-request-id": "r",
            "baggage": "user=123,env=prod",
        }
        oh = ObservabilityHeaders.from_headers(headers)
        assert oh.baggage["user"] == "123"
        assert oh.baggage["env"] == "prod"

    def test_from_headers_empty_generates_ids(self):
        oh = ObservabilityHeaders.from_headers({})
        assert oh.request_id  # auto-generated
        assert oh.trace_id  # auto-generated
        assert oh.span_id  # auto-generated


# ---------------------------------------------------------------------------
# ServiceDiscovery (async, in-memory)
# ---------------------------------------------------------------------------


class TestServiceDiscovery:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _ep(self, host="localhost", port=8080):
        return ServiceEndpoint(host=host, port=port)

    def test_register_and_get_all(self):
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc-a", "v1", [self._ep()]))
        assert len(sd.get_all_services()) == 1

    def test_register_returns_registration(self):
        sd = ServiceDiscovery()
        reg = self._run(sd.register_service("svc-a", "v1", [self._ep()]))
        assert reg.name == "svc-a"
        assert reg.version == "v1"

    def test_deregister(self):
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc-a", "v1", [self._ep()]))
        result = self._run(sd.deregister_service("svc-a", "v1"))
        assert result is True
        assert len(sd.get_all_services()) == 0

    def test_deregister_nonexistent(self):
        sd = ServiceDiscovery()
        result = self._run(sd.deregister_service("no-svc", "v1"))
        assert result is False

    def test_heartbeat(self):
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc-a", "v1", [self._ep()]))
        result = self._run(sd.heartbeat("svc-a", "v1"))
        assert result is True

    def test_heartbeat_nonexistent(self):
        sd = ServiceDiscovery()
        result = self._run(sd.heartbeat("no-svc", "v1"))
        assert result is False

    def test_discover_by_name(self):
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc-a", "v1", [self._ep()]))
        self._run(sd.register_service("svc-b", "v1", [self._ep()]))
        results = self._run(sd.discover_service("svc-a"))
        assert len(results) == 1
        assert results[0].name == "svc-a"

    def test_discover_by_version(self):
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc", "v1", [self._ep()]))
        self._run(sd.register_service("svc", "v2", [self._ep()]))
        results = self._run(sd.discover_service("svc", version="v2"))
        assert len(results) == 1
        assert results[0].version == "v2"

    def test_discover_by_tags(self):
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc", "v1", [self._ep()], tags=["critical"]))
        self._run(sd.register_service("svc", "v2", [self._ep()], tags=["test"]))
        results = self._run(sd.discover_service("svc", tags=["critical"]))
        assert len(results) == 1

    def test_discover_excludes_stale(self):
        sd = ServiceDiscovery(heartbeat_timeout_seconds=1)
        self._run(sd.register_service("svc", "v1", [self._ep()]))
        # Make it stale
        sd.services["svc:v1"].last_heartbeat = datetime.now(UTC) - timedelta(seconds=10)
        results = self._run(sd.discover_service("svc"))
        assert len(results) == 0

    def test_cleanup_stale(self):
        sd = ServiceDiscovery(heartbeat_timeout_seconds=1)
        self._run(sd.register_service("svc", "v1", [self._ep()]))
        sd.services["svc:v1"].last_heartbeat = datetime.now(UTC) - timedelta(seconds=10)
        removed = self._run(sd.cleanup_stale_services())
        assert removed == 1
        assert len(sd.get_all_services()) == 0

    def test_cleanup_nothing_stale(self):
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc", "v1", [self._ep()]))
        removed = self._run(sd.cleanup_stale_services())
        assert removed == 0

    def test_get_healthy_endpoints(self):
        ep = ServiceEndpoint(host="h1", port=80, health_status=HealthStatus.HEALTHY)
        sd = ServiceDiscovery()
        self._run(sd.register_service("svc", "v1", [ep]))
        endpoints = self._run(sd.get_healthy_endpoints("svc"))
        assert len(endpoints) == 1
        assert endpoints[0].host == "h1"

    def test_get_healthy_endpoints_empty(self):
        sd = ServiceDiscovery()
        endpoints = self._run(sd.get_healthy_endpoints("no-svc"))
        assert endpoints == []


# ---------------------------------------------------------------------------
# ServiceHealthReporter
# ---------------------------------------------------------------------------


class TestServiceHealthReporter:
    def test_creation(self):
        shr = ServiceHealthReporter("svc", "v1")
        assert shr.service_name == "svc"
        assert shr.version == "v1"
        assert shr.health_status == HealthStatus.UNKNOWN
        assert shr.last_check is None

    def test_set_health_status(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.set_health_status(HealthStatus.HEALTHY)
        assert shr.health_status == HealthStatus.HEALTHY
        assert shr.last_check is not None

    def test_add_health_check_all_pass(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.add_health_check("db", True)
        shr.add_health_check("cache", True)
        assert shr.health_status == HealthStatus.HEALTHY

    def test_add_health_check_some_fail(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.add_health_check("db", True)
        shr.add_health_check("cache", False)
        assert shr.health_status == HealthStatus.DEGRADED

    def test_add_health_check_all_fail(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.add_health_check("db", False)
        shr.add_health_check("cache", False)
        assert shr.health_status == HealthStatus.UNHEALTHY

    def test_update_overall_no_checks(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr._update_overall_status()
        assert shr.health_status == HealthStatus.UNKNOWN

    def test_get_health_report(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.add_health_check("db", True)
        report = shr.get_health_report()
        assert report["service"] == "svc"
        assert report["version"] == "v1"
        assert report["status"] == "healthy"
        assert report["checks"]["db"] is True

    def test_is_healthy(self):
        shr = ServiceHealthReporter("svc", "v1")
        assert shr.is_healthy() is False
        shr.set_health_status(HealthStatus.HEALTHY)
        assert shr.is_healthy() is True

    def test_is_ready_healthy(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.set_health_status(HealthStatus.HEALTHY)
        assert shr.is_ready() is True

    def test_is_ready_degraded(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.set_health_status(HealthStatus.DEGRADED)
        assert shr.is_ready() is True

    def test_is_ready_unhealthy(self):
        shr = ServiceHealthReporter("svc", "v1")
        shr.set_health_status(HealthStatus.UNHEALTHY)
        assert shr.is_ready() is False

    def test_is_ready_unknown(self):
        shr = ServiceHealthReporter("svc", "v1")
        assert shr.is_ready() is False


# ---------------------------------------------------------------------------
# ServiceMesh
# ---------------------------------------------------------------------------


class TestServiceMesh:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_creation(self):
        sm = ServiceMesh("test-svc")
        assert sm.service_name == "test-svc"
        assert sm.service_version == "v1"
        assert sm.routing_rules == {}
        assert sm.traffic_splits == {}

    def test_add_routing_rule(self):
        sm = ServiceMesh("svc")
        rule = RoutingRule(name="route-1", destination="dest-a")
        sm.add_routing_rule(rule)
        assert "route-1" in sm.routing_rules

    def test_add_traffic_split(self):
        sm = ServiceMesh("svc")
        split = TrafficSplit(
            id=uuid4(),
            name="canary",
            service_name="svc",
            weights=[TrafficWeight(service_version="v1", weight=100)],
        )
        sm.add_traffic_split(split)
        assert "canary" in sm.traffic_splits

    def test_get_routing_destination_prefix_match(self):
        sm = ServiceMesh("svc")
        sm.add_routing_rule(
            RoutingRule(
                name="api-route",
                destination="api-svc",
                destination_subset="v1",
                match_uri_prefix="/api",
            )
        )
        result = sm.get_routing_destination("/api/users", {})
        assert result == ("api-svc", "v1")

    def test_get_routing_destination_no_match(self):
        sm = ServiceMesh("svc")
        sm.add_routing_rule(
            RoutingRule(
                name="api-route",
                destination="api-svc",
                match_uri_prefix="/api",
            )
        )
        result = sm.get_routing_destination("/health", {})
        assert result is None

    def test_get_routing_destination_header_match(self):
        sm = ServiceMesh("svc")
        sm.add_routing_rule(
            RoutingRule(
                name="canary",
                destination="svc",
                destination_subset="v2",
                match_headers={"x-canary": "true"},
            )
        )
        result = sm.get_routing_destination("/", {"x-canary": "true"})
        assert result == ("svc", "v2")

    def test_get_routing_destination_header_no_match(self):
        sm = ServiceMesh("svc")
        sm.add_routing_rule(
            RoutingRule(
                name="canary",
                destination="svc",
                destination_subset="v2",
                match_headers={"x-canary": "true"},
            )
        )
        result = sm.get_routing_destination("/", {"x-canary": "false"})
        assert result is None

    def test_get_routing_destination_priority(self):
        sm = ServiceMesh("svc")
        sm.add_routing_rule(
            RoutingRule(
                name="low",
                destination="low-svc",
                priority=0,
            )
        )
        sm.add_routing_rule(
            RoutingRule(
                name="high",
                destination="high-svc",
                priority=10,
            )
        )
        result = sm.get_routing_destination("/anything", {})
        assert result[0] == "high-svc"

    def test_get_routing_destination_regex(self):
        sm = ServiceMesh("svc")
        sm.add_routing_rule(
            RoutingRule(
                name="regex-route",
                destination="api-svc",
                match_uri_regex=r"/api/v\d+/.*",
            )
        )
        result = sm.get_routing_destination("/api/v2/users", {})
        assert result == ("api-svc", "")

    def test_get_stats(self):
        sm = ServiceMesh("svc", "v2")
        stats = sm.get_stats()
        assert stats["service"] == "svc"
        assert stats["version"] == "v2"
        assert stats["registered_services"] == 0
        assert stats["routing_rules"] == 0
        assert stats["traffic_splits"] == 0
        assert "health" in stats

    def test_register_and_deregister(self):
        sm = ServiceMesh("svc")
        ep = ServiceEndpoint(host="localhost", port=8080)
        self._run(sm.register([ep]))
        assert len(sm.discovery.get_all_services()) == 1
        result = self._run(sm.deregister())
        assert result is True
        assert len(sm.discovery.get_all_services()) == 0

    def test_heartbeat(self):
        sm = ServiceMesh("svc")
        ep = ServiceEndpoint(host="localhost", port=8080)
        self._run(sm.register([ep]))
        result = self._run(sm.heartbeat())
        assert result is True

    def test_propagate_headers(self):
        """Note: from_headers uses ternary with 'traceparent' check.
        B3 headers (x-b3-traceid, x-b3-spanid) are only read when
        'traceparent' is present in headers. Without it, IDs are random."""
        sm = ServiceMesh("svc")
        # Include traceparent so from_headers actually reads B3 headers
        incoming = {
            "x-request-id": "req-1",
            "x-b3-traceid": "trace-1",
            "x-b3-spanid": "span-1",
            "traceparent": "00-trace-1-span-1-01",
        }
        outgoing = sm.propagate_headers(incoming)
        assert outgoing["x-b3-traceid"] == "trace-1"
        assert outgoing["x-b3-spanid"] != "span-1"  # child span
        assert outgoing["x-b3-parentspanid"] == "span-1"
