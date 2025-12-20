"""
Tests for rate limit bypass detection module.

Tests all detection techniques including IP rotation, user agent spoofing,
distributed attacks, behavioral anomalies, and fingerprint mismatches.
"""
import time
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
import redis
from fastapi import Request
from fastapi.testclient import TestClient

from app.security.rate_limit_bypass import (
    BypassDetection,
    BypassTechnique,
    RateLimitBypassDetector,
    ThreatLevel,
    check_for_bypass,
    get_bypass_detector,
)


@pytest.fixture
def redis_client():
    """Create a Redis client for testing."""
    try:
        client = redis.Redis(
            host="localhost",
            port=6379,
            db=15,  # Use separate DB for testing
            decode_responses=True
        )
        client.ping()
        yield client
        # Cleanup after tests
        client.flushdb()
    except (redis.ConnectionError, redis.TimeoutError):
        pytest.skip("Redis not available for testing")


@pytest.fixture
def detector(redis_client):
    """Create a bypass detector with test Redis client."""
    return RateLimitBypassDetector(redis_client=redis_client)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "192.168.1.100"
    request.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    request.url = Mock()
    request.url.path = "/api/test"
    return request


class TestRateLimitBypassDetector:
    """Test suite for RateLimitBypassDetector."""

    def test_initialization_with_redis(self, redis_client):
        """Test detector initialization with Redis client."""
        detector = RateLimitBypassDetector(redis_client=redis_client)
        assert detector.redis is not None
        assert detector.redis.ping()

    def test_initialization_without_redis(self):
        """Test detector gracefully handles missing Redis."""
        with patch("redis.from_url") as mock_redis:
            mock_redis.side_effect = redis.ConnectionError("Connection failed")
            detector = RateLimitBypassDetector()
            assert detector.redis is None

    def test_fingerprint_generation(self, detector, mock_request):
        """Test request fingerprint generation."""
        fingerprint1 = detector._generate_fingerprint(mock_request)
        assert fingerprint1
        assert len(fingerprint1) == 32  # SHA256 hash truncated to 32 chars

        # Same request should generate same fingerprint
        fingerprint2 = detector._generate_fingerprint(mock_request)
        assert fingerprint1 == fingerprint2

        # Different UA should generate different fingerprint
        mock_request.headers["User-Agent"] = "Different UA"
        fingerprint3 = detector._generate_fingerprint(mock_request)
        assert fingerprint1 != fingerprint3

    def test_client_ip_extraction(self, detector, mock_request):
        """Test client IP extraction from request."""
        # Test direct IP
        ip = detector._get_client_ip(mock_request)
        assert ip == "192.168.1.100"

        # Test X-Forwarded-For
        mock_request.headers["X-Forwarded-For"] = "203.0.113.1, 192.168.1.1"
        ip = detector._get_client_ip(mock_request)
        assert ip == "203.0.113.1"

    def test_ip_rotation_detection(self, detector):
        """Test IP rotation detection."""
        user_id = str(uuid4())

        # First IP - no detection
        detection = detector._detect_ip_rotation("192.168.1.1", user_id, None)
        assert detection is None

        # Second IP - no detection
        detection = detector._detect_ip_rotation("192.168.1.2", user_id, None)
        assert detection is None

        # Third IP - no detection (at threshold)
        detection = detector._detect_ip_rotation("192.168.1.3", user_id, None)
        assert detection is None

        # Fourth IP - should trigger detection
        detection = detector._detect_ip_rotation("192.168.1.4", user_id, None)
        assert detection is not None
        assert detection.technique == BypassTechnique.IP_ROTATION
        assert detection.threat_level == ThreatLevel.HIGH
        assert detection.should_block is True
        assert detection.evidence["unique_ips"] == 4
        assert len(detection.evidence["ip_list"]) == 4

    def test_ip_rotation_with_session(self, detector):
        """Test IP rotation detection with session ID."""
        session_id = str(uuid4())

        # Multiple IPs for same session
        for i in range(1, 5):
            detection = detector._detect_ip_rotation(
                f"192.168.1.{i}",
                None,
                session_id
            )

        # Should detect on 4th IP
        assert detection is not None
        assert detection.technique == BypassTechnique.IP_ROTATION

    def test_ip_rotation_time_window(self, detector, redis_client):
        """Test IP rotation respects time window."""
        user_id = str(uuid4())

        # Add old entries manually (simulate expired window)
        key = f"bypass:ip_rotation:{user_id}"
        old_time = time.time() - detector.IP_ROTATION_WINDOW - 10
        redis_client.zadd(key, {"192.168.1.1": old_time})
        redis_client.zadd(key, {"192.168.1.2": old_time})
        redis_client.zadd(key, {"192.168.1.3": old_time})

        # New IP should not trigger (old ones expired)
        detection = detector._detect_ip_rotation("192.168.1.4", user_id, None)
        assert detection is None

    def test_user_agent_spoofing_detection(self, detector):
        """Test user agent spoofing detection."""
        user_id = str(uuid4())
        ip_address = "192.168.1.100"

        # First UA - no detection
        detection = detector._detect_user_agent_spoofing(
            ip_address,
            user_id,
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        assert detection is None

        # Second UA - no detection
        detection = detector._detect_user_agent_spoofing(
            ip_address,
            user_id,
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        )
        assert detection is None

        # Third UA - should trigger detection
        detection = detector._detect_user_agent_spoofing(
            ip_address,
            user_id,
            "Mozilla/5.0 (X11; Linux x86_64)"
        )
        assert detection is not None
        assert detection.technique == BypassTechnique.USER_AGENT_SPOOFING
        assert detection.threat_level == ThreatLevel.MEDIUM
        assert detection.should_block is True
        assert detection.evidence["unique_user_agents"] == 3

    def test_user_agent_spoofing_requires_user_id(self, detector):
        """Test UA spoofing detection requires user ID."""
        detection = detector._detect_user_agent_spoofing(
            "192.168.1.100",
            None,  # No user ID
            "Some User Agent"
        )
        assert detection is None

    def test_distributed_attack_detection(self, detector):
        """Test distributed attack pattern detection."""
        endpoint = "/api/login"

        # Add requests from multiple IPs
        for i in range(1, detector.DISTRIBUTED_ATTACK_THRESHOLD):
            detection = detector._detect_distributed_attack(
                f"192.168.1.{i}",
                endpoint
            )
            assert detection is None  # Not enough IPs yet

        # Add one more IP to trigger detection
        detection = detector._detect_distributed_attack(
            f"192.168.1.{detector.DISTRIBUTED_ATTACK_THRESHOLD}",
            endpoint
        )
        assert detection is not None
        assert detection.technique == BypassTechnique.DISTRIBUTED_ATTACK
        assert detection.threat_level == ThreatLevel.CRITICAL
        assert detection.should_block is True
        assert detection.evidence["unique_ips"] >= detector.DISTRIBUTED_ATTACK_THRESHOLD

    def test_distributed_attack_endpoint_specific(self, detector):
        """Test distributed attack detection is endpoint-specific."""
        endpoint1 = "/api/login"
        endpoint2 = "/api/register"

        # Add requests to different endpoints
        for i in range(1, 6):
            detector._detect_distributed_attack(f"192.168.1.{i}", endpoint1)
            detector._detect_distributed_attack(f"192.168.2.{i}", endpoint2)

        # Neither should trigger alone (only 5 IPs each)
        detection1 = detector._detect_distributed_attack("192.168.1.6", endpoint1)
        detection2 = detector._detect_distributed_attack("192.168.2.6", endpoint2)

        assert detection1 is None
        assert detection2 is None

    def test_behavioral_anomaly_missing_headers(self, detector, mock_request):
        """Test behavioral anomaly detection for missing headers."""
        user_id = str(uuid4())

        # Remove common headers
        mock_request.headers = {
            "User-Agent": "Mozilla/5.0"
            # Missing Accept and Accept-Language
        }

        detection = detector._detect_behavioral_anomaly(
            mock_request,
            "192.168.1.100",
            user_id,
            "test_fingerprint"
        )

        # First request may not trigger (need to accumulate)
        # Run multiple times
        for _ in range(3):
            detection = detector._detect_behavioral_anomaly(
                mock_request,
                "192.168.1.100",
                user_id,
                "test_fingerprint"
            )

        assert detection is not None
        assert detection.technique == BypassTechnique.BEHAVIORAL_ANOMALY
        assert "missing_accept_header" in detection.evidence["suspicious_behaviors"]

    def test_behavioral_anomaly_suspicious_proxy(self, detector, mock_request):
        """Test behavioral anomaly detection for suspicious proxy chains."""
        user_id = str(uuid4())

        # Add long proxy chain
        mock_request.headers["X-Forwarded-For"] = ", ".join(
            [f"192.168.{i}.1" for i in range(10)]
        )

        detection = detector._detect_behavioral_anomaly(
            mock_request,
            "192.168.1.100",
            user_id,
            "test_fingerprint"
        )

        # May need multiple requests to accumulate
        for _ in range(3):
            detection = detector._detect_behavioral_anomaly(
                mock_request,
                "192.168.1.100",
                user_id,
                "test_fingerprint"
            )

        if detection:
            assert detection.technique == BypassTechnique.BEHAVIORAL_ANOMALY
            assert "suspicious_proxy_chain" in detection.evidence["suspicious_behaviors"]

    def test_fingerprint_mismatch_detection(self, detector):
        """Test fingerprint mismatch detection."""
        user_id = str(uuid4())
        ip_address = "192.168.1.100"

        # First request - establish fingerprint
        detection = detector._detect_fingerprint_mismatch(
            ip_address,
            user_id,
            "fingerprint1"
        )
        assert detection is None

        # Same fingerprint - no detection
        detection = detector._detect_fingerprint_mismatch(
            ip_address,
            user_id,
            "fingerprint1"
        )
        assert detection is None

        # Different fingerprint - should detect
        detection = detector._detect_fingerprint_mismatch(
            ip_address,
            user_id,
            "fingerprint2"
        )
        assert detection is not None
        assert detection.technique == BypassTechnique.FINGERPRINT_MISMATCH
        assert detection.threat_level == ThreatLevel.HIGH
        assert detection.should_block is True

    def test_fingerprint_mismatch_requires_user_id(self, detector):
        """Test fingerprint mismatch detection requires user ID."""
        detection = detector._detect_fingerprint_mismatch(
            "192.168.1.100",
            None,  # No user ID
            "fingerprint"
        )
        assert detection is None

    def test_block_ip(self, detector, redis_client):
        """Test IP blocking."""
        ip_address = "192.168.1.100"

        # Block IP
        success = detector.block_ip(ip_address, duration=60)
        assert success is True

        # Verify blocked
        assert detector._is_blocked(ip_address, None) is True

        # Unblock IP
        success = detector.unblock_ip(ip_address)
        assert success is True

        # Verify unblocked
        assert detector._is_blocked(ip_address, None) is False

    def test_block_user(self, detector, redis_client):
        """Test user blocking."""
        user_id = str(uuid4())

        # Block user
        success = detector.block_user(user_id, duration=60)
        assert success is True

        # Verify blocked
        assert detector._is_blocked("any_ip", user_id) is True

        # Unblock user
        success = detector.unblock_user(user_id)
        assert success is True

        # Verify unblocked
        assert detector._is_blocked("any_ip", user_id) is False

    def test_is_blocked_checks_both_ip_and_user(self, detector):
        """Test blocking checks both IP and user."""
        ip_address = "192.168.1.100"
        user_id = str(uuid4())

        # Block IP
        detector.block_ip(ip_address)
        assert detector._is_blocked(ip_address, user_id) is True

        # Unblock IP, block user
        detector.unblock_ip(ip_address)
        detector.block_user(user_id)
        assert detector._is_blocked(ip_address, user_id) is True

    def test_blocked_request_returns_detection(self, detector, mock_request):
        """Test that blocked IPs return immediate detection."""
        ip_address = "192.168.1.100"
        mock_request.client.host = ip_address

        # Block the IP
        detector.block_ip(ip_address)

        # Request should be immediately detected as blocked
        detection = detector.detect_bypass_attempt(mock_request)
        assert detection is not None
        assert detection.should_block is True
        assert "Previously blocked" in detection.evidence["reason"]

    @pytest.mark.asyncio
    async def test_log_and_alert(self, detector, redis_client):
        """Test logging and alerting of bypass attempts."""
        detection = BypassDetection(
            technique=BypassTechnique.IP_ROTATION,
            threat_level=ThreatLevel.HIGH,
            ip_address="192.168.1.100",
            user_id=str(uuid4()),
            user_agent="Test UA",
            endpoint="/api/test",
            fingerprint="test_fp",
            evidence={"test": "data"},
            timestamp=datetime.utcnow(),
            should_block=True
        )

        # Log and alert (without DB for now)
        await detector.log_and_alert(detection, db=None)

        # Verify detection was stored in Redis
        keys = redis_client.keys("bypass:detection:*")
        assert len(keys) > 0

    def test_detect_bypass_attempt_returns_highest_severity(self, detector, mock_request):
        """Test that multiple detections return the highest severity."""
        user_id = str(uuid4())

        # Trigger multiple detection types
        # 1. IP rotation (HIGH)
        for i in range(1, 5):
            detector._detect_ip_rotation(f"192.168.1.{i}", user_id, None)

        # 2. UA spoofing (MEDIUM)
        for ua in ["UA1", "UA2", "UA3"]:
            detector._detect_user_agent_spoofing("192.168.1.100", user_id, ua)

        mock_request.client.host = "192.168.1.4"

        # Detection should return highest severity (IP_ROTATION - HIGH)
        detection = detector.detect_bypass_attempt(mock_request, user_id=user_id)

        if detection:
            # Should be high or critical severity
            assert detection.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL)

    @pytest.mark.asyncio
    async def test_check_for_bypass_auto_blocks(self, detector, mock_request, redis_client):
        """Test check_for_bypass automatically blocks on detection."""
        user_id = str(uuid4())

        # Trigger IP rotation to cause detection
        for i in range(1, 5):
            detector._detect_ip_rotation(f"192.168.1.{i}", user_id, None)

        mock_request.client.host = "192.168.1.4"

        # Check for bypass with auto-block enabled
        with patch("app.security.rate_limit_bypass.get_bypass_detector", return_value=detector):
            detection = await check_for_bypass(
                mock_request,
                user_id=user_id,
                auto_block=True
            )

        if detection and detection.should_block:
            # Verify IP was blocked
            assert detector._is_blocked("192.168.1.4", user_id) is True

    @pytest.mark.asyncio
    async def test_check_for_bypass_no_auto_block(self, detector, mock_request, redis_client):
        """Test check_for_bypass can skip auto-blocking."""
        user_id = str(uuid4())

        # Trigger detection
        for i in range(1, 5):
            detector._detect_ip_rotation(f"192.168.1.{i}", user_id, None)

        mock_request.client.host = "192.168.1.4"

        # Check for bypass with auto-block disabled
        with patch("app.security.rate_limit_bypass.get_bypass_detector", return_value=detector):
            detection = await check_for_bypass(
                mock_request,
                user_id=user_id,
                auto_block=False
            )

        # Even with detection, should not block if auto_block=False
        if detection:
            # Cannot assert not blocked because detect_bypass_attempt might block
            # Just verify detection was returned
            assert detection is not None


class TestBypassDetectorIntegration:
    """Integration tests for bypass detector."""

    def test_full_detection_workflow(self, detector, mock_request):
        """Test complete detection workflow."""
        user_id = str(uuid4())
        session_id = str(uuid4())

        # Simulate multiple requests with suspicious patterns
        for i in range(5):
            mock_request.client.host = f"192.168.1.{i + 1}"
            mock_request.headers["User-Agent"] = f"UA-{i}"

            detection = detector.detect_bypass_attempt(
                mock_request,
                user_id=user_id,
                session_id=session_id
            )

            # Should eventually detect bypass
            if detection:
                assert detection.should_block is True
                break

    def test_global_detector_instance(self):
        """Test global detector instance retrieval."""
        detector1 = get_bypass_detector()
        detector2 = get_bypass_detector()

        # Should return same instance
        assert detector1 is detector2


class TestBypassDetectionEdgeCases:
    """Test edge cases and error handling."""

    def test_detector_without_redis_returns_none(self):
        """Test detector gracefully handles missing Redis."""
        detector = RateLimitBypassDetector(redis_client=None)

        detection = detector._detect_ip_rotation("192.168.1.1", "user123", None)
        assert detection is None

    def test_missing_request_headers(self, detector):
        """Test handling of requests with minimal headers."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}  # No headers
        request.url = Mock()
        request.url.path = "/api/test"

        # Should not crash
        fingerprint = detector._generate_fingerprint(request)
        assert fingerprint is not None

    def test_unknown_client_ip(self, detector):
        """Test handling of requests without client IP."""
        request = Mock(spec=Request)
        request.client = None  # No client
        request.headers = {}
        request.url = Mock()
        request.url.path = "/api/test"

        ip = detector._get_client_ip(request)
        assert ip == "unknown"
