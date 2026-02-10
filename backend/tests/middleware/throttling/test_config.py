"""Tests for request throttling configuration (no DB)."""

from __future__ import annotations

import pytest

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


# ---------------------------------------------------------------------------
# ThrottlePriority enum
# ---------------------------------------------------------------------------


class TestThrottlePriority:
    def test_values(self):
        assert ThrottlePriority.CRITICAL == "critical"
        assert ThrottlePriority.HIGH == "high"
        assert ThrottlePriority.NORMAL == "normal"
        assert ThrottlePriority.LOW == "low"
        assert ThrottlePriority.BACKGROUND == "background"

    def test_count(self):
        assert len(ThrottlePriority) == 5

    def test_is_string_enum(self):
        assert isinstance(ThrottlePriority.CRITICAL, str)


# ---------------------------------------------------------------------------
# ThrottleConfig dataclass
# ---------------------------------------------------------------------------


class TestThrottleConfig:
    def test_construction(self):
        cfg = ThrottleConfig(
            max_concurrent_requests=10,
            max_queue_size=20,
            queue_timeout_seconds=5.0,
        )
        assert cfg.max_concurrent_requests == 10
        assert cfg.max_queue_size == 20
        assert cfg.queue_timeout_seconds == 5.0
        assert cfg.enabled is True

    def test_disabled(self):
        cfg = ThrottleConfig(
            max_concurrent_requests=10,
            max_queue_size=20,
            queue_timeout_seconds=5.0,
            enabled=False,
        )
        assert cfg.enabled is False


# ---------------------------------------------------------------------------
# EndpointThrottleConfig dataclass
# ---------------------------------------------------------------------------


class TestEndpointThrottleConfig:
    def test_construction(self):
        cfg = EndpointThrottleConfig(
            endpoint_pattern="/api/test",
            max_concurrent=5,
            max_queue_size=10,
            queue_timeout=30.0,
        )
        assert cfg.endpoint_pattern == "/api/test"
        assert cfg.max_concurrent == 5
        assert cfg.priority == ThrottlePriority.NORMAL

    def test_custom_priority(self):
        cfg = EndpointThrottleConfig(
            endpoint_pattern="/api/test",
            max_concurrent=5,
            max_queue_size=10,
            queue_timeout=30.0,
            priority=ThrottlePriority.CRITICAL,
        )
        assert cfg.priority == ThrottlePriority.CRITICAL


# ---------------------------------------------------------------------------
# UserThrottleConfig dataclass
# ---------------------------------------------------------------------------


class TestUserThrottleConfig:
    def test_construction(self):
        cfg = UserThrottleConfig(
            user_id="user1",
            max_concurrent=5,
            max_queue_size=10,
            queue_timeout=15.0,
        )
        assert cfg.user_id == "user1"
        assert cfg.priority_boost is False

    def test_priority_boost(self):
        cfg = UserThrottleConfig(
            user_id="admin1",
            max_concurrent=50,
            max_queue_size=100,
            queue_timeout=60.0,
            priority_boost=True,
        )
        assert cfg.priority_boost is True


# ---------------------------------------------------------------------------
# DEFAULT_THROTTLE_CONFIG
# ---------------------------------------------------------------------------


class TestDefaultConfig:
    def test_enabled(self):
        assert DEFAULT_THROTTLE_CONFIG.enabled is True

    def test_concurrent_positive(self):
        assert DEFAULT_THROTTLE_CONFIG.max_concurrent_requests > 0

    def test_queue_positive(self):
        assert DEFAULT_THROTTLE_CONFIG.max_queue_size > 0

    def test_timeout_positive(self):
        assert DEFAULT_THROTTLE_CONFIG.queue_timeout_seconds > 0


# ---------------------------------------------------------------------------
# ENDPOINT_THROTTLE_CONFIGS
# ---------------------------------------------------------------------------


class TestEndpointConfigs:
    def test_health_is_critical(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/health"]
        assert cfg.priority == ThrottlePriority.CRITICAL

    def test_metrics_is_critical(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/metrics"]
        assert cfg.priority == ThrottlePriority.CRITICAL

    def test_generate_is_high(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/schedules/generate"]
        assert cfg.priority == ThrottlePriority.HIGH

    def test_generate_limited_concurrency(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/schedules/generate"]
        assert cfg.max_concurrent <= 10  # Expensive operation

    def test_analytics_is_low(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/analytics/*"]
        assert cfg.priority == ThrottlePriority.LOW

    def test_reports_is_background(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/reports/*"]
        assert cfg.priority == ThrottlePriority.BACKGROUND

    def test_persons_is_normal(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/persons/*"]
        assert cfg.priority == ThrottlePriority.NORMAL

    def test_health_no_queuing(self):
        cfg = ENDPOINT_THROTTLE_CONFIGS["/api/v1/health"]
        assert cfg.max_queue_size == 0

    def test_all_configs_positive_concurrency(self):
        for pattern, cfg in ENDPOINT_THROTTLE_CONFIGS.items():
            assert cfg.max_concurrent > 0, f"{pattern} has zero concurrency"


# ---------------------------------------------------------------------------
# ROLE_THROTTLE_LIMITS
# ---------------------------------------------------------------------------


class TestRoleThrottleLimits:
    def test_all_8_roles(self):
        expected_roles = {
            "ADMIN",
            "COORDINATOR",
            "FACULTY",
            "RESIDENT",
            "CLINICAL_STAFF",
            "RN",
            "LPN",
            "MSA",
        }
        assert set(ROLE_THROTTLE_LIMITS.keys()) == expected_roles

    def test_admin_highest_concurrency(self):
        admin = ROLE_THROTTLE_LIMITS["ADMIN"]
        for role, cfg in ROLE_THROTTLE_LIMITS.items():
            assert admin.max_concurrent_requests >= cfg.max_concurrent_requests

    def test_admin_longest_timeout(self):
        admin = ROLE_THROTTLE_LIMITS["ADMIN"]
        for role, cfg in ROLE_THROTTLE_LIMITS.items():
            assert admin.queue_timeout_seconds >= cfg.queue_timeout_seconds

    def test_all_configs_valid(self):
        for role, cfg in ROLE_THROTTLE_LIMITS.items():
            assert cfg.max_concurrent_requests > 0, f"{role} has zero concurrency"
            assert cfg.max_queue_size > 0, f"{role} has zero queue"
            assert cfg.queue_timeout_seconds > 0, f"{role} has zero timeout"


# ---------------------------------------------------------------------------
# DEGRADATION_THRESHOLDS
# ---------------------------------------------------------------------------


class TestDegradationThresholds:
    def test_four_levels(self):
        assert len(DEGRADATION_THRESHOLDS) == 4

    def test_ordering(self):
        assert DEGRADATION_THRESHOLDS["warning"] < DEGRADATION_THRESHOLDS["throttle"]
        assert DEGRADATION_THRESHOLDS["throttle"] < DEGRADATION_THRESHOLDS["reject"]
        assert DEGRADATION_THRESHOLDS["reject"] < DEGRADATION_THRESHOLDS["critical"]

    def test_all_between_0_and_1(self):
        for level, threshold in DEGRADATION_THRESHOLDS.items():
            assert 0.0 < threshold < 1.0, f"{level} threshold out of range"

    def test_critical_near_100(self):
        assert DEGRADATION_THRESHOLDS["critical"] >= 0.90


# ---------------------------------------------------------------------------
# get_endpoint_config — exact match
# ---------------------------------------------------------------------------


class TestGetEndpointConfigExact:
    def test_exact_match(self):
        cfg = get_endpoint_config("/api/v1/health")
        assert cfg is not None
        assert cfg.priority == ThrottlePriority.CRITICAL

    def test_exact_generate(self):
        cfg = get_endpoint_config("/api/v1/schedules/generate")
        assert cfg is not None
        assert cfg.priority == ThrottlePriority.HIGH

    def test_no_match(self):
        assert get_endpoint_config("/api/v99/unknown") is None


# ---------------------------------------------------------------------------
# get_endpoint_config — pattern (glob) match
# ---------------------------------------------------------------------------


class TestGetEndpointConfigPattern:
    def test_analytics_glob(self):
        cfg = get_endpoint_config("/api/v1/analytics/dashboard")
        assert cfg is not None
        assert cfg.priority == ThrottlePriority.LOW

    def test_reports_glob(self):
        cfg = get_endpoint_config("/api/v1/reports/monthly")
        assert cfg is not None
        assert cfg.priority == ThrottlePriority.BACKGROUND

    def test_persons_glob(self):
        cfg = get_endpoint_config("/api/v1/persons/123")
        assert cfg is not None
        assert cfg.priority == ThrottlePriority.NORMAL

    def test_assignments_glob(self):
        cfg = get_endpoint_config("/api/v1/assignments/bulk")
        assert cfg is not None
        assert cfg.priority == ThrottlePriority.NORMAL


# ---------------------------------------------------------------------------
# get_role_config
# ---------------------------------------------------------------------------


class TestGetRoleConfig:
    def test_admin(self):
        cfg = get_role_config("ADMIN")
        assert cfg.max_concurrent_requests == 50

    def test_faculty(self):
        cfg = get_role_config("FACULTY")
        assert cfg.max_concurrent_requests == 20

    def test_unknown_role_returns_default(self):
        cfg = get_role_config("UNKNOWN")
        assert cfg is DEFAULT_THROTTLE_CONFIG

    def test_none_returns_default(self):
        cfg = get_role_config(None)
        assert cfg is DEFAULT_THROTTLE_CONFIG

    def test_empty_returns_default(self):
        cfg = get_role_config("")
        assert cfg is DEFAULT_THROTTLE_CONFIG


# ---------------------------------------------------------------------------
# get_priority_for_endpoint
# ---------------------------------------------------------------------------


class TestGetPriorityForEndpoint:
    def test_health_critical(self):
        assert get_priority_for_endpoint("/api/v1/health") == ThrottlePriority.CRITICAL

    def test_generate_high(self):
        assert (
            get_priority_for_endpoint("/api/v1/schedules/generate")
            == ThrottlePriority.HIGH
        )

    def test_analytics_low(self):
        assert (
            get_priority_for_endpoint("/api/v1/analytics/any") == ThrottlePriority.LOW
        )

    def test_unknown_defaults_normal(self):
        assert get_priority_for_endpoint("/api/v99/unknown") == ThrottlePriority.NORMAL
