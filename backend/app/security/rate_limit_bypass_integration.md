***REMOVED*** Rate Limit Bypass Detection Integration Guide

This guide explains how to integrate the rate limit bypass detection system into the Residency Scheduler backend.

***REMOVED******REMOVED*** Overview

The `rate_limit_bypass.py` module provides advanced detection and prevention of rate limit bypass attempts through:

- **IP Rotation Detection**: Detects when a user/session rapidly switches between multiple IP addresses
- **User Agent Spoofing Detection**: Identifies suspicious user agent changes
- **Distributed Attack Pattern Recognition**: Detects coordinated attacks from multiple IPs
- **Behavioral Anomaly Detection**: Flags unusual request patterns (missing headers, rapid requests, etc.)
- **Fingerprint-based Tracking**: Uses browser fingerprinting to track clients across sessions
- **Automatic Blocking**: Temporarily blocks suspicious IPs and users
- **Alert System**: Integrates with the notification system for security alerts

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Basic Usage

```python
from fastapi import Request, HTTPException, Depends
from app.security.rate_limit_bypass import check_for_bypass
from app.api.deps import get_current_user_optional

@router.post("/api/login")
async def login(
    request: Request,
    credentials: LoginCredentials,
    current_user = Depends(get_current_user_optional)
):
    ***REMOVED*** Check for bypass attempts
    user_id = str(current_user.id) if current_user else None
    detection = await check_for_bypass(
        request,
        user_id=user_id,
        auto_block=True  ***REMOVED*** Automatically block on detection
    )

    if detection and detection.should_block:
        raise HTTPException(
            status_code=403,
            detail="Access denied due to suspicious activity"
        )

    ***REMOVED*** Continue with normal login logic
    ...
```

***REMOVED******REMOVED******REMOVED*** Middleware Integration

For application-wide protection, add as middleware:

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.security.rate_limit_bypass import check_for_bypass

class BypassDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware to detect rate limit bypass attempts."""

    async def dispatch(self, request: Request, call_next):
        ***REMOVED*** Skip bypass detection for health checks and static files
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        ***REMOVED*** Check for bypass attempts
        detection = await check_for_bypass(
            request,
            auto_block=True
        )

        if detection and detection.should_block:
            ***REMOVED*** Log security event
            logger.warning(
                f"Blocked request: {detection.technique.value} "
                f"from {detection.ip_address}"
            )

            ***REMOVED*** Return 403 Forbidden
            return Response(
                content=json.dumps({
                    "detail": "Access denied due to suspicious activity"
                }),
                status_code=403,
                media_type="application/json"
            )

        ***REMOVED*** Continue processing
        response = await call_next(request)
        return response

***REMOVED*** Add to app
app = FastAPI()
app.add_middleware(BypassDetectionMiddleware)
```

***REMOVED******REMOVED******REMOVED*** Manual Detection

For fine-grained control, use the detector directly:

```python
from app.security.rate_limit_bypass import (
    get_bypass_detector,
    BypassTechnique,
    ThreatLevel
)

detector = get_bypass_detector()

@router.post("/api/sensitive-operation")
async def sensitive_operation(request: Request):
    ***REMOVED*** Detect bypass attempts
    detection = detector.detect_bypass_attempt(
        request,
        user_id="user-123",
        session_id="session-456"
    )

    if detection:
        ***REMOVED*** Check threat level
        if detection.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
            ***REMOVED*** Block immediately for high/critical threats
            detector.block_ip(detection.ip_address)
            if detection.user_id:
                detector.block_user(detection.user_id)

            ***REMOVED*** Send alert
            await detector.log_and_alert(detection, db=db)

            raise HTTPException(status_code=403, detail="Access denied")

        elif detection.threat_level == ThreatLevel.MEDIUM:
            ***REMOVED*** Log but allow for medium threats
            logger.warning(f"Medium threat detected: {detection.technique.value}")

    ***REMOVED*** Continue processing
    ...
```

***REMOVED******REMOVED*** Detection Techniques

***REMOVED******REMOVED******REMOVED*** 1. IP Rotation Detection

Detects when a user/session switches between multiple IPs rapidly.

**Threshold**: 3 unique IPs in 5 minutes
**Threat Level**: HIGH
**Auto-block**: Yes

**Example Attack Pattern**:
```
User "alice" makes requests from:
- 192.168.1.1 at 10:00:00
- 192.168.1.2 at 10:01:00
- 192.168.1.3 at 10:02:00
- 192.168.1.4 at 10:03:00  <- DETECTED (4th IP)
```

***REMOVED******REMOVED******REMOVED*** 2. User Agent Spoofing Detection

Identifies when a user changes their user agent string frequently.

**Threshold**: 2 unique user agents in 5 minutes
**Threat Level**: MEDIUM
**Auto-block**: Yes

**Example Attack Pattern**:
```
User "bob" sends requests with:
- UA: "Mozilla/5.0 (Windows...)" at 10:00:00
- UA: "Mozilla/5.0 (Macintosh...)" at 10:01:00
- UA: "Mozilla/5.0 (Linux...)" at 10:02:00  <- DETECTED (3rd UA)
```

***REMOVED******REMOVED******REMOVED*** 3. Distributed Attack Detection

Detects coordinated attacks from multiple IPs targeting the same endpoint.

**Threshold**: 10 unique IPs in 1 minute
**Threat Level**: CRITICAL
**Auto-block**: Yes

**Example Attack Pattern**:
```
Endpoint /api/login receives requests from:
- 192.168.1.1, 192.168.1.2, ..., 192.168.1.10 in 60 seconds
- DETECTED as distributed attack
```

***REMOVED******REMOVED******REMOVED*** 4. Behavioral Anomaly Detection

Flags unusual request patterns based on multiple signals:
- Missing common headers (Accept, Accept-Language)
- Suspicious proxy chains (>5 IPs in X-Forwarded-For)
- Rapid sequential requests (>20 in 10 seconds)

**Threshold**: 5 suspicious behaviors in 5 minutes
**Threat Level**: MEDIUM
**Auto-block**: Yes

***REMOVED******REMOVED******REMOVED*** 5. Fingerprint Mismatch Detection

Detects when a user's browser fingerprint changes unexpectedly, indicating session hijacking or spoofing.

**Threshold**: Fingerprint change for authenticated user
**Threat Level**: HIGH
**Auto-block**: Yes

**Fingerprint Components**:
- User-Agent
- Accept headers
- Accept-Language
- Accept-Encoding
- Chrome client hints (Sec-CH-UA-*)

***REMOVED******REMOVED*** Configuration

Default thresholds can be customized:

```python
from app.security.rate_limit_bypass import RateLimitBypassDetector

detector = RateLimitBypassDetector()

***REMOVED*** Customize thresholds
detector.IP_ROTATION_THRESHOLD = 5  ***REMOVED*** Allow 5 IPs instead of 3
detector.IP_ROTATION_WINDOW = 600  ***REMOVED*** 10 minutes instead of 5
detector.DISTRIBUTED_ATTACK_THRESHOLD = 20  ***REMOVED*** Require 20 IPs
detector.BLOCK_DURATION = 7200  ***REMOVED*** Block for 2 hours instead of 1
```

***REMOVED******REMOVED*** Blocking and Unblocking

***REMOVED******REMOVED******REMOVED*** Block an IP

```python
detector = get_bypass_detector()
detector.block_ip("192.168.1.100", duration=3600)  ***REMOVED*** Block for 1 hour
```

***REMOVED******REMOVED******REMOVED*** Block a User

```python
detector.block_user("user-123", duration=7200)  ***REMOVED*** Block for 2 hours
```

***REMOVED******REMOVED******REMOVED*** Unblock

```python
detector.unblock_ip("192.168.1.100")
detector.unblock_user("user-123")
```

***REMOVED******REMOVED******REMOVED*** Check Block Status

```python
is_blocked = detector._is_blocked("192.168.1.100", "user-123")
```

***REMOVED******REMOVED*** Logging and Alerts

The system automatically logs all bypass attempts and can send alerts for high/critical threats.

```python
detection = detector.detect_bypass_attempt(request)
if detection:
    ***REMOVED*** Log and send alerts
    await detector.log_and_alert(detection, db=db)
```

**Log Output**:
```
WARNING - Rate limit bypass detected: ip_rotation (threat: high)
from IP 192.168.1.100 (user: user-123)
```

**Redis Storage**:
- Detections are stored in Redis with key pattern: `bypass:detection:{ip}:{timestamp}`
- Stored for 24 hours for analysis
- Can be queried for security audits

***REMOVED******REMOVED*** Integration with Existing Rate Limiter

The bypass detector works alongside the existing rate limiter (`app.core.rate_limit`):

```python
from app.core.rate_limit import create_rate_limit_dependency
from app.security.rate_limit_bypass import check_for_bypass

***REMOVED*** Apply both rate limiting and bypass detection
rate_limit_login = create_rate_limit_dependency(
    max_requests=5,
    window_seconds=60,
    key_prefix="login"
)

@router.post("/api/login")
async def login(
    request: Request,
    _rate_limit: None = Depends(rate_limit_login)  ***REMOVED*** Rate limit
):
    ***REMOVED*** Bypass detection
    detection = await check_for_bypass(request, auto_block=True)
    if detection and detection.should_block:
        raise HTTPException(status_code=403, detail="Access denied")

    ***REMOVED*** Process login
    ...
```

***REMOVED******REMOVED*** Best Practices

1. **Apply to sensitive endpoints**: Focus on login, registration, password reset, and data modification endpoints

2. **Use appropriate auto-blocking**: Enable auto-block for high/critical threats, consider manual review for medium/low

3. **Monitor alerts**: Integrate with notification system to alert admins of security events

4. **Tune thresholds**: Adjust thresholds based on your application's usage patterns

5. **Whitelist trusted IPs**: Consider bypassing detection for known good IPs (VPN servers, office networks)

6. **Review blocked entities**: Periodically review blocked IPs/users to identify false positives

7. **Combine with rate limiting**: Use bypass detection alongside traditional rate limiting for defense in depth

***REMOVED******REMOVED*** Testing

Run the test suite to verify functionality:

```bash
cd backend
pytest tests/security/test_rate_limit_bypass.py -v
```

***REMOVED******REMOVED*** Performance Considerations

- **Redis dependency**: Requires Redis for tracking patterns
- **Minimal overhead**: Uses Redis pipelines and caching for efficiency
- **Graceful degradation**: Falls back to allow requests if Redis is unavailable
- **Time complexity**: O(1) for most operations, O(log N) for Redis sorted set operations

***REMOVED******REMOVED*** Security Considerations

- **Defense in depth**: Use as part of a layered security strategy
- **False positives**: Tune thresholds to minimize blocking legitimate users
- **Logging**: All detections are logged for audit trails
- **Privacy**: IP addresses and user IDs are logged but not exposed to clients
- **Rate of change**: Detection adapts to attack patterns in real-time

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** High false positive rate

- Increase detection thresholds
- Reduce block duration
- Review behavioral anomaly triggers

***REMOVED******REMOVED******REMOVED*** Redis connection errors

- Verify Redis is running and accessible
- Check Redis authentication credentials
- Review network connectivity

***REMOVED******REMOVED******REMOVED*** Detections not triggering

- Verify Redis is properly configured
- Check that requests include necessary headers
- Review detection thresholds (may be too high)

***REMOVED******REMOVED*** Future Enhancements

Potential improvements for future versions:

- Machine learning-based anomaly detection
- Geo-location based risk scoring
- Integration with threat intelligence feeds
- Adaptive thresholds based on baseline traffic
- CAPTCHA challenges for suspicious requests
- Rate limit bypass attempt metrics/dashboard

***REMOVED******REMOVED*** References

- Rate Limiting: `backend/app/core/rate_limit.py`
- Security Headers: `backend/app/security/middleware.py`
- Notifications: `backend/app/notifications/service.py`
- Configuration: `backend/app/core/config.py`
