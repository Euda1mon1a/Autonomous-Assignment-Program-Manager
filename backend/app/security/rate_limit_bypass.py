"""
Rate limit bypass detection and prevention module.

Implements advanced detection techniques to identify and block attempts to bypass
rate limiting through IP rotation, user agent spoofing, distributed attacks, and
other evasion tactics. Uses behavioral analysis and fingerprinting to detect
sophisticated attack patterns.

Features:
- IP rotation detection: Tracks rapid IP changes per user/session
- User agent spoofing detection: Identifies suspicious UA changes
- Distributed attack pattern recognition: Detects coordinated attacks
- Behavioral anomaly detection: Flags unusual request patterns
- Fingerprint-based tracking: Combines multiple signals for robust tracking
- Automatic blocking: Temporarily blocks suspicious IPs and users
- Alert system: Integrates with notification system for security alerts
"""

import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import redis
from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BypassTechnique(str, Enum):
    """Types of bypass techniques detected."""

    IP_ROTATION = "ip_rotation"
    USER_AGENT_SPOOFING = "user_agent_spoofing"
    DISTRIBUTED_ATTACK = "distributed_attack"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    RATE_LIMIT_EVASION = "rate_limit_evasion"
    SESSION_HIJACKING = "session_hijacking"


class ThreatLevel(str, Enum):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BypassDetection:
    """
    Details of a detected bypass attempt.

    Attributes:
        technique: The bypass technique detected
        threat_level: Severity of the threat
        ip_address: Source IP address
        user_id: User ID if authenticated
        user_agent: User agent string
        endpoint: Target endpoint
        fingerprint: Request fingerprint
        evidence: Additional evidence of the bypass attempt
        timestamp: When the attempt was detected
        should_block: Whether to block this request
    """

    technique: BypassTechnique
    threat_level: ThreatLevel
    ip_address: str
    user_id: str | None
    user_agent: str
    endpoint: str
    fingerprint: str
    evidence: dict
    timestamp: datetime
    should_block: bool


class RateLimitBypassDetector:
    """
    Advanced rate limit bypass detection system.

    Uses multiple detection techniques and behavioral analysis to identify
    and prevent sophisticated attempts to bypass rate limiting.
    """

    # Detection thresholds (configurable)
    IP_ROTATION_THRESHOLD = 3  # Max IPs per user in time window
    IP_ROTATION_WINDOW = 300  # 5 minutes
    UA_CHANGE_THRESHOLD = 2  # Max UA changes per user in time window
    UA_CHANGE_WINDOW = 300  # 5 minutes
    DISTRIBUTED_ATTACK_THRESHOLD = 10  # Min IPs targeting same endpoint
    DISTRIBUTED_ATTACK_WINDOW = 60  # 1 minute
    BEHAVIORAL_ANOMALY_THRESHOLD = 5  # Max suspicious behaviors
    BEHAVIORAL_ANOMALY_WINDOW = 300  # 5 minutes
    BLOCK_DURATION = 3600  # 1 hour block duration

    def __init__(self, redis_client: redis.Redis | None = None):
        """
        Initialize the bypass detector.

        Args:
            redis_client: Optional Redis client. If not provided, creates a new one.
        """
        if redis_client is None:
            try:
                redis_url = settings.redis_url_with_password
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                self.redis.ping()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.error(f"Failed to connect to Redis for bypass detection: {e}")
                self.redis = None
        else:
            self.redis = redis_client

        # In-memory cache for performance (temporary storage)
        self._fingerprint_cache: dict[str, str] = {}
        self._detection_cache: dict[str, list[BypassDetection]] = defaultdict(list)

    def detect_bypass_attempt(
        self,
        request: Request,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> BypassDetection | None:
        """
        Analyze a request for bypass attempts using multiple detection techniques.

        Args:
            request: FastAPI request object
            user_id: Optional authenticated user ID
            session_id: Optional session identifier

        Returns:
            BypassDetection object if bypass detected, None otherwise
        """
        if self.redis is None:
            return None

        # Extract request metadata
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        endpoint = request.url.path
        fingerprint = self._generate_fingerprint(request)

        # Check if already blocked
        if self._is_blocked(ip_address, user_id):
            logger.warning(
                f"Blocked request from IP {ip_address} (user: {user_id or 'anonymous'})"
            )
            return BypassDetection(
                technique=BypassTechnique.RATE_LIMIT_EVASION,
                threat_level=ThreatLevel.HIGH,
                ip_address=ip_address,
                user_id=user_id,
                user_agent=user_agent,
                endpoint=endpoint,
                fingerprint=fingerprint,
                evidence={"reason": "Previously blocked for bypass attempts"},
                timestamp=datetime.utcnow(),
                should_block=True,
            )

        # Run detection techniques in order of severity
        detections = []

        # 1. IP rotation detection
        ip_rotation = self._detect_ip_rotation(ip_address, user_id, session_id)
        if ip_rotation:
            detections.append(ip_rotation)

        # 2. User agent spoofing detection
        ua_spoofing = self._detect_user_agent_spoofing(ip_address, user_id, user_agent)
        if ua_spoofing:
            detections.append(ua_spoofing)

        # 3. Distributed attack detection
        distributed = self._detect_distributed_attack(ip_address, endpoint)
        if distributed:
            detections.append(distributed)

        # 4. Behavioral anomaly detection
        behavioral = self._detect_behavioral_anomaly(
            request, ip_address, user_id, fingerprint
        )
        if behavioral:
            detections.append(behavioral)

        # 5. Fingerprint mismatch detection
        fingerprint_mismatch = self._detect_fingerprint_mismatch(
            ip_address, user_id, fingerprint
        )
        if fingerprint_mismatch:
            detections.append(fingerprint_mismatch)

        # Return highest severity detection
        if detections:
            # Sort by threat level (critical > high > medium > low)
            threat_order = {
                ThreatLevel.CRITICAL: 4,
                ThreatLevel.HIGH: 3,
                ThreatLevel.MEDIUM: 2,
                ThreatLevel.LOW: 1,
            }
            detections.sort(
                key=lambda d: threat_order.get(d.threat_level, 0), reverse=True
            )
            return detections[0]

        return None

    def _detect_ip_rotation(
        self, ip_address: str, user_id: str | None, session_id: str | None
    ) -> BypassDetection | None:
        """
        Detect IP rotation by tracking IP changes per user/session.

        Args:
            ip_address: Client IP address
            user_id: Optional user ID
            session_id: Optional session ID

        Returns:
            BypassDetection if rotation detected, None otherwise
        """
        if not user_id and not session_id:
            return None

        try:
            identifier = user_id or session_id
            key = f"bypass:ip_rotation:{identifier}"
            current_time = time.time()

            # Add current IP with timestamp
            self.redis.zadd(key, {ip_address: current_time})
            self.redis.expire(key, self.IP_ROTATION_WINDOW)

            # Remove old entries
            cutoff = current_time - self.IP_ROTATION_WINDOW
            self.redis.zremrangebyscore(key, 0, cutoff)

            # Count unique IPs
            unique_ips = self.redis.zcard(key)
            ip_list = self.redis.zrange(key, 0, -1)

            if unique_ips > self.IP_ROTATION_THRESHOLD:
                logger.warning(
                    f"IP rotation detected for {identifier}: "
                    f"{unique_ips} IPs in {self.IP_ROTATION_WINDOW}s"
                )
                return BypassDetection(
                    technique=BypassTechnique.IP_ROTATION,
                    threat_level=ThreatLevel.HIGH,
                    ip_address=ip_address,
                    user_id=user_id,
                    user_agent="",
                    endpoint="",
                    fingerprint="",
                    evidence={
                        "unique_ips": unique_ips,
                        "ip_list": list(ip_list),
                        "window_seconds": self.IP_ROTATION_WINDOW,
                    },
                    timestamp=datetime.utcnow(),
                    should_block=True,
                )

        except Exception as e:
            logger.error(f"Error in IP rotation detection: {e}")

        return None

    def _detect_user_agent_spoofing(
        self, ip_address: str, user_id: str | None, user_agent: str
    ) -> BypassDetection | None:
        """
        Detect user agent spoofing by tracking UA changes.

        Args:
            ip_address: Client IP address
            user_id: Optional user ID
            user_agent: User agent string

        Returns:
            BypassDetection if spoofing detected, None otherwise
        """
        if not user_id:
            return None

        try:
            key = f"bypass:user_agent:{user_id}"
            current_time = time.time()

            # Hash user agent for storage efficiency
            ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

            # Add current UA with timestamp
            self.redis.zadd(key, {ua_hash: current_time})
            self.redis.expire(key, self.UA_CHANGE_WINDOW)

            # Remove old entries
            cutoff = current_time - self.UA_CHANGE_WINDOW
            self.redis.zremrangebyscore(key, 0, cutoff)

            # Count unique user agents
            unique_uas = self.redis.zcard(key)

            if unique_uas > self.UA_CHANGE_THRESHOLD:
                logger.warning(
                    f"User agent spoofing detected for user {user_id}: "
                    f"{unique_uas} different UAs in {self.UA_CHANGE_WINDOW}s"
                )
                return BypassDetection(
                    technique=BypassTechnique.USER_AGENT_SPOOFING,
                    threat_level=ThreatLevel.MEDIUM,
                    ip_address=ip_address,
                    user_id=user_id,
                    user_agent=user_agent,
                    endpoint="",
                    fingerprint="",
                    evidence={
                        "unique_user_agents": unique_uas,
                        "window_seconds": self.UA_CHANGE_WINDOW,
                    },
                    timestamp=datetime.utcnow(),
                    should_block=True,
                )

        except Exception as e:
            logger.error(f"Error in user agent spoofing detection: {e}")

        return None

    def _detect_distributed_attack(
        self, ip_address: str, endpoint: str
    ) -> BypassDetection | None:
        """
        Detect distributed attacks by tracking multiple IPs targeting same endpoint.

        Args:
            ip_address: Client IP address
            endpoint: Target endpoint

        Returns:
            BypassDetection if distributed attack detected, None otherwise
        """
        try:
            key = f"bypass:distributed:{endpoint}"
            current_time = time.time()

            # Add current IP with timestamp
            self.redis.zadd(key, {ip_address: current_time})
            self.redis.expire(key, self.DISTRIBUTED_ATTACK_WINDOW)

            # Remove old entries
            cutoff = current_time - self.DISTRIBUTED_ATTACK_WINDOW
            self.redis.zremrangebyscore(key, 0, cutoff)

            # Count unique IPs targeting this endpoint
            unique_ips = self.redis.zcard(key)

            if unique_ips >= self.DISTRIBUTED_ATTACK_THRESHOLD:
                ip_list = self.redis.zrange(key, 0, -1)
                logger.warning(
                    f"Distributed attack detected on {endpoint}: "
                    f"{unique_ips} IPs in {self.DISTRIBUTED_ATTACK_WINDOW}s"
                )
                return BypassDetection(
                    technique=BypassTechnique.DISTRIBUTED_ATTACK,
                    threat_level=ThreatLevel.CRITICAL,
                    ip_address=ip_address,
                    user_id=None,
                    user_agent="",
                    endpoint=endpoint,
                    fingerprint="",
                    evidence={
                        "unique_ips": unique_ips,
                        "attacking_ips": list(ip_list)[:20],  # Limit for logging
                        "window_seconds": self.DISTRIBUTED_ATTACK_WINDOW,
                    },
                    timestamp=datetime.utcnow(),
                    should_block=True,
                )

        except Exception as e:
            logger.error(f"Error in distributed attack detection: {e}")

        return None

    def _detect_behavioral_anomaly(
        self, request: Request, ip_address: str, user_id: str | None, fingerprint: str
    ) -> BypassDetection | None:
        """
        Detect behavioral anomalies using multiple signals.

        Args:
            request: FastAPI request object
            ip_address: Client IP address
            user_id: Optional user ID
            fingerprint: Request fingerprint

        Returns:
            BypassDetection if anomaly detected, None otherwise
        """
        try:
            identifier = user_id or ip_address
            key = f"bypass:behavioral:{identifier}"
            current_time = time.time()

            # Track suspicious behaviors
            suspicious_count = 0
            behaviors = []

            # Check for missing common headers
            if not request.headers.get("Accept"):
                suspicious_count += 1
                behaviors.append("missing_accept_header")

            if not request.headers.get("Accept-Language"):
                suspicious_count += 1
                behaviors.append("missing_accept_language")

            # Check for unusual header patterns
            if request.headers.get("X-Forwarded-For"):
                xff_ips = request.headers.get("X-Forwarded-For", "").split(",")
                if len(xff_ips) > 5:  # Suspicious proxy chain
                    suspicious_count += 1
                    behaviors.append("suspicious_proxy_chain")

            # Check for rapid sequential requests (store in Redis)
            request_key = f"{key}:requests"
            self.redis.zadd(request_key, {str(current_time): current_time})
            self.redis.expire(request_key, 10)  # 10 second window

            # Remove old entries
            self.redis.zremrangebyscore(request_key, 0, current_time - 10)

            # Count requests in last 10 seconds
            request_count = self.redis.zcard(request_key)
            if request_count > 20:  # More than 20 requests in 10 seconds
                suspicious_count += 2
                behaviors.append(f"rapid_requests:{request_count}")

            # Store behavior count
            if suspicious_count > 0:
                self.redis.zadd(
                    key, {f"{current_time}:{suspicious_count}": current_time}
                )
                self.redis.expire(key, self.BEHAVIORAL_ANOMALY_WINDOW)

                # Remove old entries
                cutoff = current_time - self.BEHAVIORAL_ANOMALY_WINDOW
                self.redis.zremrangebyscore(key, 0, cutoff)

                # Sum suspicious behaviors in window
                entries = self.redis.zrange(key, 0, -1)
                total_suspicious = sum(
                    int(entry.split(":")[-1]) for entry in entries if ":" in entry
                )

                if total_suspicious >= self.BEHAVIORAL_ANOMALY_THRESHOLD:
                    logger.warning(
                        f"Behavioral anomaly detected for {identifier}: "
                        f"{total_suspicious} suspicious behaviors"
                    )
                    return BypassDetection(
                        technique=BypassTechnique.BEHAVIORAL_ANOMALY,
                        threat_level=ThreatLevel.MEDIUM,
                        ip_address=ip_address,
                        user_id=user_id,
                        user_agent=request.headers.get("User-Agent", ""),
                        endpoint=request.url.path,
                        fingerprint=fingerprint,
                        evidence={
                            "suspicious_behaviors": behaviors,
                            "total_count": total_suspicious,
                            "window_seconds": self.BEHAVIORAL_ANOMALY_WINDOW,
                        },
                        timestamp=datetime.utcnow(),
                        should_block=True,
                    )

        except Exception as e:
            logger.error(f"Error in behavioral anomaly detection: {e}")

        return None

    def _detect_fingerprint_mismatch(
        self, ip_address: str, user_id: str | None, fingerprint: str
    ) -> BypassDetection | None:
        """
        Detect fingerprint mismatches indicating session hijacking or spoofing.

        Args:
            ip_address: Client IP address
            user_id: Optional user ID
            fingerprint: Request fingerprint

        Returns:
            BypassDetection if mismatch detected, None otherwise
        """
        if not user_id:
            return None

        try:
            key = f"bypass:fingerprint:{user_id}"
            stored_fingerprint = self.redis.get(key)

            if stored_fingerprint and stored_fingerprint != fingerprint:
                logger.warning(
                    f"Fingerprint mismatch for user {user_id}: "
                    f"expected {stored_fingerprint}, got {fingerprint}"
                )
                return BypassDetection(
                    technique=BypassTechnique.FINGERPRINT_MISMATCH,
                    threat_level=ThreatLevel.HIGH,
                    ip_address=ip_address,
                    user_id=user_id,
                    user_agent="",
                    endpoint="",
                    fingerprint=fingerprint,
                    evidence={
                        "expected_fingerprint": stored_fingerprint,
                        "actual_fingerprint": fingerprint,
                    },
                    timestamp=datetime.utcnow(),
                    should_block=True,
                )
            else:
                # Store fingerprint for future comparison (24 hour expiry)
                self.redis.setex(key, 86400, fingerprint)

        except Exception as e:
            logger.error(f"Error in fingerprint mismatch detection: {e}")

        return None

    def _generate_fingerprint(self, request: Request) -> str:
        """
        Generate a unique fingerprint for a request based on multiple signals.

        Args:
            request: FastAPI request object

        Returns:
            Fingerprint hash string
        """
        # Combine multiple signals for fingerprinting
        signals = [
            request.headers.get("User-Agent", ""),
            request.headers.get("Accept", ""),
            request.headers.get("Accept-Language", ""),
            request.headers.get("Accept-Encoding", ""),
            request.headers.get("Sec-CH-UA", ""),  # Chrome client hints
            request.headers.get("Sec-CH-UA-Platform", ""),
        ]

        # Create fingerprint hash
        fingerprint_data = "|".join(signals)
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]

        return fingerprint

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address as string
        """
        # Check X-Forwarded-For header (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (client IP)
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _is_blocked(self, ip_address: str, user_id: str | None) -> bool:
        """
        Check if an IP or user is currently blocked.

        Args:
            ip_address: Client IP address
            user_id: Optional user ID

        Returns:
            True if blocked, False otherwise
        """
        if self.redis is None:
            return False

        try:
            # Check IP block
            ip_blocked = self.redis.get(f"bypass:block:ip:{ip_address}")
            if ip_blocked:
                return True

            # Check user block
            if user_id:
                user_blocked = self.redis.get(f"bypass:block:user:{user_id}")
                if user_blocked:
                    return True

        except Exception as e:
            logger.error(f"Error checking block status: {e}")

        return False

    def block_ip(self, ip_address: str, duration: int | None = None) -> bool:
        """
        Block an IP address for a specified duration.

        Args:
            ip_address: IP address to block
            duration: Block duration in seconds (default: BLOCK_DURATION)

        Returns:
            True if successful, False otherwise
        """
        if self.redis is None:
            return False

        try:
            block_duration = duration or self.BLOCK_DURATION
            key = f"bypass:block:ip:{ip_address}"
            self.redis.setex(key, block_duration, "1")
            logger.info(f"Blocked IP {ip_address} for {block_duration} seconds")
            return True
        except Exception as e:
            logger.error(f"Failed to block IP {ip_address}: {e}")
            return False

    def block_user(self, user_id: str, duration: int | None = None) -> bool:
        """
        Block a user for a specified duration.

        Args:
            user_id: User ID to block
            duration: Block duration in seconds (default: BLOCK_DURATION)

        Returns:
            True if successful, False otherwise
        """
        if self.redis is None:
            return False

        try:
            block_duration = duration or self.BLOCK_DURATION
            key = f"bypass:block:user:{user_id}"
            self.redis.setex(key, block_duration, "1")
            logger.info(f"Blocked user {user_id} for {block_duration} seconds")
            return True
        except Exception as e:
            logger.error(f"Failed to block user {user_id}: {e}")
            return False

    def unblock_ip(self, ip_address: str) -> bool:
        """
        Unblock an IP address.

        Args:
            ip_address: IP address to unblock

        Returns:
            True if successful, False otherwise
        """
        if self.redis is None:
            return False

        try:
            key = f"bypass:block:ip:{ip_address}"
            self.redis.delete(key)
            logger.info(f"Unblocked IP {ip_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip_address}: {e}")
            return False

    def unblock_user(self, user_id: str) -> bool:
        """
        Unblock a user.

        Args:
            user_id: User ID to unblock

        Returns:
            True if successful, False otherwise
        """
        if self.redis is None:
            return False

        try:
            key = f"bypass:block:user:{user_id}"
            self.redis.delete(key)
            logger.info(f"Unblocked user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unblock user {user_id}: {e}")
            return False

    async def log_and_alert(
        self, detection: BypassDetection, db: Session | None = None
    ) -> None:
        """
        Log bypass attempt and send alerts.

        Args:
            detection: BypassDetection object
            db: Optional database session for sending notifications
        """
        # Log to application logger
        logger.warning(
            f"Rate limit bypass detected: {detection.technique.value} "
            f"(threat: {detection.threat_level.value}) "
            f"from IP {detection.ip_address} "
            f"(user: {detection.user_id or 'anonymous'})"
        )

        # Store detection in Redis for tracking
        try:
            if self.redis:
                key = f"bypass:detection:{detection.ip_address}:{int(time.time())}"
                detection_data = {
                    "technique": detection.technique.value,
                    "threat_level": detection.threat_level.value,
                    "user_id": detection.user_id or "",
                    "endpoint": detection.endpoint,
                    "timestamp": detection.timestamp.isoformat(),
                }
                self.redis.hmset(key, detection_data)
                self.redis.expire(key, 86400)  # Keep for 24 hours
        except Exception as e:
            logger.error(f"Failed to store detection in Redis: {e}")

        # Send alert notification for high/critical threats
        if detection.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL) and db:
            try:
                # Get admin users to notify (would need to query from DB)
                # For now, just log - in production, would send to admins
                logger.critical(
                    f"SECURITY ALERT: {detection.technique.value} detected - "
                    f"IP: {detection.ip_address}, User: {detection.user_id or 'anonymous'}, "
                    f"Evidence: {detection.evidence}"
                )
            except Exception as e:
                logger.error(f"Failed to send security alert: {e}")


# Global bypass detector instance
_bypass_detector: RateLimitBypassDetector | None = None


def get_bypass_detector() -> RateLimitBypassDetector:
    """
    Get or create the global bypass detector instance.

    Returns:
        RateLimitBypassDetector instance
    """
    global _bypass_detector
    if _bypass_detector is None:
        _bypass_detector = RateLimitBypassDetector()
    return _bypass_detector


async def check_for_bypass(
    request: Request,
    user_id: str | None = None,
    session_id: str | None = None,
    auto_block: bool = True,
    db: Session | None = None,
) -> BypassDetection | None:
    """
    Check a request for rate limit bypass attempts.

    This is the main entry point for bypass detection. Use this in middleware
    or as a dependency in route handlers.

    Args:
        request: FastAPI request object
        user_id: Optional authenticated user ID
        session_id: Optional session identifier
        auto_block: Automatically block on detection (default: True)
        db: Optional database session for notifications

    Returns:
        BypassDetection object if bypass detected, None otherwise

    Example:
        ```python
        from app.security.rate_limit_bypass import check_for_bypass

        @router.post("/api/sensitive-endpoint")
        async def sensitive_endpoint(request: Request):
            detection = await check_for_bypass(request)
            if detection and detection.should_block:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied due to suspicious activity"
                )
            # Process request normally
        ```
    """
    detector = get_bypass_detector()
    detection = detector.detect_bypass_attempt(request, user_id, session_id)

    if detection:
        # Log and alert
        await detector.log_and_alert(detection, db)

        # Auto-block if enabled and detection warrants it
        if auto_block and detection.should_block:
            if detection.ip_address and detection.ip_address != "unknown":
                detector.block_ip(detection.ip_address)

            if detection.user_id:
                detector.block_user(detection.user_id)

    return detection
