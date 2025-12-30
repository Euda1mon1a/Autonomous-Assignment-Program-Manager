# Rate Limiting Security Audit

**Audit Date:** 2025-12-30
**Auditor:** AI Security Analysis
**Scope:** Rate limiting implementation across authentication, API endpoints, and file uploads
**System:** Residency Scheduler - Medical Residency Scheduling Application

---

## Executive Summary

The Residency Scheduler implements a **multi-layered, defense-in-depth rate limiting strategy** with strong protection against brute force attacks, API abuse, and distributed attacks. The implementation uses industry best practices including:

- ✅ **Sliding window algorithm** for accurate rate limiting
- ✅ **Token bucket algorithm** for burst handling
- ✅ **Per-user account lockout** with exponential backoff
- ✅ **Tiered rate limits** based on user roles
- ✅ **Per-endpoint custom limits** for expensive operations
- ✅ **Graceful degradation** when Redis is unavailable
- ✅ **Comprehensive test coverage**

**Overall Security Rating:** ⭐⭐⭐⭐ (4/5) - **Strong**

**Critical Findings:** None
**High Priority Gaps:** 2
**Medium Priority Gaps:** 3
**Low Priority Gaps:** 2

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Rate Limiting Implementation](#rate-limiting-implementation)
3. [Protected Endpoints](#protected-endpoints)
4. [Configuration Review](#configuration-review)
5. [Security Gaps](#security-gaps)
6. [Recommendations](#recommendations)
7. [Testing Coverage](#testing-coverage)
8. [Compliance Notes](#compliance-notes)

---

## Architecture Overview

### Multi-Layer Defense Strategy

The system implements **three independent layers** of rate limiting:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: SlowAPI Middleware (Global)                       │
│  - Applied via @limiter.limit() decorators                  │
│  - Uses slowapi library for FastAPI                         │
│  - Configurable per-endpoint limits                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Tiered Rate Limiting (RateLimitMiddleware)       │
│  - Token bucket for burst handling                          │
│  - Sliding window for sustained rate                        │
│  - Role-based tier assignment (FREE → ADMIN)                │
│  - Per-endpoint overrides                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Account Lockout (Authentication Only)            │
│  - Username-based lockout (not IP-based)                    │
│  - Exponential backoff: 1m → 2m → 4m → ... → 60m           │
│  - Prevents distributed brute force                         │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Storage** | Redis (Sorted Sets + Hashes) | Atomic operations, sliding windows |
| **Algorithms** | Sliding Window + Token Bucket | Accurate rate limiting + burst handling |
| **Middleware** | SlowAPI + Custom Middleware | Global and tiered enforcement |
| **Fallback** | Fail-open design | Graceful degradation when Redis unavailable |

---

## Rate Limiting Implementation

### 1. Core RateLimiter Class

**Location:** `backend/app/core/rate_limit.py`

#### Features

- **Sliding Window Algorithm**: Uses Redis sorted sets with timestamps as scores
- **Atomic Operations**: Redis pipelines ensure race-free counting
- **Graceful Degradation**: Fails open if Redis unavailable (allows requests)
- **IP Extraction**: Handles X-Forwarded-For with trusted proxy validation

#### Key Methods

```python
is_rate_limited(key, max_requests, window_seconds) → (bool, dict)
reset(key) → bool
get_remaining(key, max_requests, window_seconds) → int
```

#### Trusted Proxy Handling

✅ **SECURE**: Only trusts X-Forwarded-For from configured trusted proxies
- Prevents header spoofing attacks
- Validates IP format and CIDR ranges
- Falls back to direct client IP if not from trusted proxy

**Configuration:**
```python
TRUSTED_PROXIES = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
```

---

### 2. Account Lockout System

**Location:** `backend/app/core/rate_limit.py` (AccountLockout class)

#### Features

- **Username-based lockout**: Independent of IP address (prevents distributed attacks)
- **Exponential backoff**: Lockout duration increases with each failed attempt
- **Configurable thresholds**: 5 failed attempts trigger initial lockout
- **Auto-reset on success**: Clears lockout on successful authentication

#### Lockout Progression

| Failed Attempts | Lockout Duration |
|----------------|------------------|
| 5 | 60 seconds (1 minute) |
| 6 | 120 seconds (2 minutes) |
| 7 | 240 seconds (4 minutes) |
| 8 | 480 seconds (8 minutes) |
| 9+ | 3600 seconds (60 minutes, max) |

#### Security Strengths

✅ **Prevents distributed brute force** - Locks account across all IPs
✅ **Exponential backoff** - Increasing cost for attackers
✅ **Separate from IP limiting** - Dual-layer defense

**Code Example:**
```python
# Check lockout before authentication
is_locked, lockout_seconds = lockout.check_lockout(username)
if is_locked:
    raise HTTPException(status_code=429, ...)

# Record failed attempt after auth failure
is_now_locked, attempts_remaining, lockout_seconds = \
    lockout.record_failed_attempt(username)

# Clear on success
lockout.clear_lockout(username)
```

---

### 3. Tiered Rate Limiting

**Location:** `backend/app/core/rate_limit_tiers.py` + `backend/app/middleware/rate_limit_middleware.py`

#### Rate Limit Tiers

| Tier | Roles | Per-Minute | Per-Hour | Burst Size |
|------|-------|-----------|----------|-----------|
| **FREE** | Unauthenticated | 10 | 100 | 5 |
| **STANDARD** | Resident, Clinical Staff, RN, LPN, MSA | 60 | 1,000 | 20 |
| **PREMIUM** | Faculty, Coordinator | 120 | 5,000 | 50 |
| **ADMIN** | Admin | 300 | 10,000 | 100 |
| **INTERNAL** | Internal Services | Unlimited | Unlimited | Unlimited |

#### Token Bucket Configuration

Uses **Lua scripts** for atomic token bucket operations:
- Capacity = burst_size
- Refill rate = requests_per_minute / 60 (tokens per second)
- TTL = 1 hour (auto-cleanup)

#### Per-Endpoint Limits

**Expensive Operations:**

| Endpoint | Per-Minute | Per-Hour | Burst | Reason |
|----------|-----------|----------|-------|--------|
| `/api/schedule/generate` | 2 | 20 | 1 | CPU-intensive solver |
| `/api/analytics/complex` | 5 | 50 | 2 | Heavy queries |
| `/api/auth/login` | 5 | 20 | 3 | Brute force prevention |
| `/api/auth/register` | 3 | 10 | 2 | Account creation abuse |

✅ **STRENGTH**: Endpoint limits override tier limits, preventing expensive operation abuse even for high-tier users

---

### 4. SlowAPI Integration

**Location:** `backend/app/main.py` + `backend/app/core/slowapi_limiter.py`

#### Implementation

```python
# Attached to app state
app.state.limiter = limiter

# Middleware
app.add_middleware(SlowAPIMiddleware)

# Exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

#### Usage Pattern

```python
from app.core.slowapi_limiter import limiter

@router.get("/expensive-operation")
@limiter.limit("5/minute")
async def expensive_operation(...):
    ...
```

**Status:** SlowAPI middleware is registered but **usage in routes is not widespread**. Most rate limiting relies on custom middleware and dependency injection.

---

## Protected Endpoints

### Authentication Endpoints

| Endpoint | Method | Rate Limit | Lockout | Status |
|----------|--------|-----------|---------|--------|
| `/api/auth/login` | POST | 5/min, 20/hr | ✅ Yes | ✅ Protected |
| `/api/auth/login/json` | POST | 5/min, 20/hr | ✅ Yes | ✅ Protected |
| `/api/auth/register` | POST | 3/min, 10/hr | ❌ No | ✅ Protected |
| `/api/auth/refresh` | POST | ❌ None | ❌ No | ⚠️ **GAP** |
| `/api/auth/logout` | POST | ❌ None | ❌ No | ✅ OK (auth required) |
| `/api/auth/me` | GET | ❌ None | ❌ No | ✅ OK (auth required) |

**Implementation:**
```python
# Rate limit dependency injection
rate_limit_login = create_rate_limit_dependency(
    max_requests=settings.RATE_LIMIT_LOGIN_ATTEMPTS,  # 5
    window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW,  # 60
    key_prefix="login",
)

@router.post("/login")
async def login(
    _rate_limit: None = Depends(rate_limit_login),
    ...
):
```

---

### File Upload Endpoints

| Endpoint | Method | Rate Limit | Status | Risk Level |
|----------|--------|-----------|--------|-----------|
| `/api/upload` | POST | ❌ None | ⚠️ **GAP** | **HIGH** |
| `/api/upload/progress/{upload_id}` | GET | ❌ None | ✅ OK | Low |
| `/api/upload/{file_id}/url` | GET | ❌ None | ✅ OK | Low |
| `/api/upload/{file_id}/download` | GET | ❌ None | ⚠️ Minor | Medium |
| `/api/upload/{file_id}` | DELETE | ❌ None | ✅ OK | Low |

**Location:** `backend/app/api/routes/upload.py`

**Current Protection:**
- ✅ Authentication required (`Depends(get_current_active_user)`)
- ✅ File size validation (max 50MB by default)
- ✅ File type whitelisting
- ❌ **NO rate limiting** - can be abused for storage/bandwidth exhaustion

---

### Admin Endpoints

| Endpoint | Method | Rate Limit | Status | Risk Level |
|----------|--------|-----------|--------|-----------|
| `/api/admin-users` | POST | ❌ None | ⚠️ **GAP** | **MEDIUM** |
| `/api/admin-users/{id}` | PUT | ❌ None | ⚠️ **GAP** | **MEDIUM** |
| `/api/admin-users/{id}` | DELETE | ❌ None | ⚠️ **GAP** | **MEDIUM** |
| `/api/admin-users/{id}/lock` | POST | ❌ None | ⚠️ Minor | Low |
| `/api/admin-users/{id}/resend-invite` | POST | ❌ None | ⚠️ Minor | Low |
| `/api/admin-users/bulk` | POST | ❌ None | ⚠️ **GAP** | **MEDIUM** |

**Location:** `backend/app/api/routes/admin_users.py`

**Current Protection:**
- ✅ Admin role required (`Depends(get_admin_user)`)
- ❌ **NO rate limiting** - malicious admin or compromised account could spam operations

---

### API Endpoints (General)

**Global Middleware Coverage:**
- ✅ RateLimitMiddleware applies to ALL requests (except bypass list)
- ✅ Tier-based limits enforce baseline protection
- ✅ Bypass for health/metrics/docs endpoints

**Bypass List:**
```python
skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]
```

**Internal Service Bypass:**
- Uses `X-Internal-Service-Key` header validation
- Key = first 32 chars of SECRET_KEY
- Only bypasses for localhost + specific paths (health, metrics)

⚠️ **CONCERN**: Internal service key is derived from SECRET_KEY, not a separate credential

---

### Webhook Endpoints

| Endpoint | Method | Rate Limit | Status |
|----------|--------|-----------|--------|
| `/api/webhooks` | POST | ❌ None | ⚠️ Minor |
| `/api/webhooks` | GET | ❌ None | ✅ OK |
| `/api/webhooks/{id}` | PUT/DELETE | ❌ None | ⚠️ Minor |

**Location:** `backend/app/api/routes/webhooks.py`

**Current Protection:**
- ✅ Authentication required
- ❌ No specific rate limits (relies on tier limits)

---

## Configuration Review

### Environment Variables

**Location:** `backend/app/core/config.py`

```python
# Rate limiting configuration
RATE_LIMIT_LOGIN_ATTEMPTS: int = 5     # Login attempts per minute
RATE_LIMIT_LOGIN_WINDOW: int = 60      # Time window (seconds)
RATE_LIMIT_REGISTER_ATTEMPTS: int = 3  # Registration per minute
RATE_LIMIT_REGISTER_WINDOW: int = 60   # Time window (seconds)
RATE_LIMIT_ENABLED: bool = True        # Global enable/disable

# Trusted proxies for X-Forwarded-For
TRUSTED_PROXIES: list[str] = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
```

### Redis Configuration

```python
# Redis connection for rate limiting
redis_url_with_password: str  # Format: redis://:password@host:port/db
```

**Timeout Settings:**
- Socket connect timeout: 5 seconds
- Socket timeout: 5 seconds
- Fail-open on timeout (allows requests)

### Account Lockout Configuration

**Hard-coded in AccountLockout class:**

```python
MAX_FAILED_ATTEMPTS: int = 5           # Lock after 5 failures
BASE_LOCKOUT_SECONDS: int = 60         # Initial lockout: 1 minute
MAX_LOCKOUT_SECONDS: int = 3600        # Maximum: 1 hour
BACKOFF_MULTIPLIER: float = 2.0        # Double each time
```

⚠️ **GAP**: Not configurable via environment variables

---

## Security Gaps

### HIGH Priority

#### 1. File Upload Rate Limiting ⚠️ **CRITICAL**

**Risk:** Storage/bandwidth exhaustion attack
**Affected Endpoints:** `POST /api/upload`

**Attack Scenario:**
1. Attacker creates valid user account
2. Uploads 50MB files repeatedly
3. Exhausts server storage/bandwidth despite tier limits (60 uploads/min for STANDARD tier)

**Recommendation:**
```python
# Add to upload.py
from app.core.rate_limit import create_rate_limit_dependency

rate_limit_upload = create_rate_limit_dependency(
    max_requests=5,        # 5 uploads per minute
    window_seconds=60,
    key_prefix="upload",
)

@router.post("")
async def upload_file(
    _rate_limit: None = Depends(rate_limit_upload),
    ...
):
```

**Impact:** High
**Effort:** Low (1-2 hours)
**Priority:** **IMMEDIATE**

---

#### 2. Token Refresh Rate Limiting ⚠️ **HIGH**

**Risk:** Token refresh abuse
**Affected Endpoint:** `POST /api/auth/refresh`

**Attack Scenario:**
1. Attacker obtains valid refresh token (e.g., via XSS or storage leak)
2. Continuously refreshes to obtain new access tokens
3. Maintains persistent access even after password change

**Current State:**
- ✅ Token rotation enabled (`REFRESH_TOKEN_ROTATE=True`)
- ✅ Blacklisting on use
- ❌ **No rate limiting** on refresh endpoint

**Recommendation:**
```python
rate_limit_refresh = create_rate_limit_dependency(
    max_requests=10,       # 10 refreshes per hour
    window_seconds=3600,
    key_prefix="refresh",
)

@router.post("/refresh")
async def refresh_token(
    _rate_limit: None = Depends(rate_limit_refresh),
    ...
):
```

**Impact:** High
**Effort:** Low (30 minutes)
**Priority:** **HIGH**

---

### MEDIUM Priority

#### 3. Admin Endpoint Rate Limiting

**Risk:** Compromised admin account abuse
**Affected Endpoints:** Admin user management operations

**Recommendation:** Add rate limits to:
- `POST /api/admin-users` - 10/minute (account creation)
- `POST /api/admin-users/bulk` - 5/minute (bulk operations)
- `DELETE /api/admin-users/{id}` - 10/minute (account deletion)

**Rationale:** Even admins should have reasonable limits to prevent automation abuse

**Impact:** Medium
**Effort:** Low (1 hour)
**Priority:** **MEDIUM**

---

#### 4. Account Lockout Configuration Externalization

**Current State:** Lockout parameters hard-coded in `AccountLockout` class

**Recommendation:** Move to environment variables:
```python
# Add to config.py
ACCOUNT_LOCKOUT_MAX_ATTEMPTS: int = 5
ACCOUNT_LOCKOUT_BASE_SECONDS: int = 60
ACCOUNT_LOCKOUT_MAX_SECONDS: int = 3600
ACCOUNT_LOCKOUT_MULTIPLIER: float = 2.0
```

**Impact:** Medium (operational flexibility)
**Effort:** Low (30 minutes)
**Priority:** **MEDIUM**

---

#### 5. Webhook Rate Limiting

**Risk:** Webhook spam (create/update operations)
**Affected Endpoints:** Webhook management

**Recommendation:**
- `POST /api/webhooks` - 10/minute
- `PUT /api/webhooks/{id}` - 20/minute
- `DELETE /api/webhooks/{id}` - 10/minute

**Impact:** Medium
**Effort:** Low (30 minutes)
**Priority:** **MEDIUM**

---

### LOW Priority

#### 6. Internal Service Key Separation

**Current State:** Internal service key derived from `SECRET_KEY[:32]`

**Recommendation:** Use separate `INTERNAL_SERVICE_KEY` environment variable

**Rationale:** Principle of least privilege - internal services shouldn't know SECRET_KEY

**Impact:** Low
**Effort:** Low (15 minutes)
**Priority:** **LOW**

---

#### 7. Rate Limit Response Headers

**Current State:** Custom rate limit responses include headers, but not standardized across all implementations

**Recommendation:** Ensure all rate limit responses include standard headers:
```
X-RateLimit-Limit: <limit>
X-RateLimit-Remaining: <remaining>
X-RateLimit-Reset: <unix-timestamp>
Retry-After: <seconds>
```

**Current Coverage:**
- ✅ SlowAPI implementation includes headers
- ✅ Custom rate limit dependency includes headers
- ✅ RateLimitMiddleware includes headers
- ✅ Account lockout includes Retry-After

**Impact:** Low (usability)
**Effort:** Low (documentation update)
**Priority:** **LOW**

---

## Recommendations

### Immediate Actions (Next Sprint)

1. **Add file upload rate limiting** (1-2 hours)
   - Implement 5/minute limit per user
   - Consider separate limit for different file sizes

2. **Add token refresh rate limiting** (30 minutes)
   - Implement 10/hour limit per refresh token

3. **Document rate limits in API docs** (1 hour)
   - Update OpenAPI schema with rate limit information
   - Add rate limiting section to README

### Short-term Improvements (1-2 Sprints)

4. **Add admin endpoint rate limiting** (1 hour)
   - Protect bulk operations
   - Protect account creation/deletion

5. **Externalize lockout configuration** (30 minutes)
   - Move to environment variables
   - Update deployment documentation

6. **Add monitoring and alerting** (2-4 hours)
   - Log rate limit violations
   - Alert on high rate limit hit rates
   - Dashboard for rate limit metrics

### Long-term Enhancements (Future)

7. **Implement adaptive rate limiting**
   - Adjust limits based on system load
   - Lower limits during high traffic periods

8. **Add user-specific custom limits**
   - API for setting per-user overrides
   - Admin UI for limit management

9. **Implement CAPTCHA for repeated failures**
   - After 3 lockouts, require CAPTCHA
   - Deters automated attacks

10. **Add distributed rate limiting**
    - If scaling to multiple backend instances
    - Consider rate limiting at load balancer/API gateway level

---

## Testing Coverage

### Unit Tests

**Location:** `backend/tests/test_rate_limiting.py`

**Coverage:**
- ✅ RateLimiter class initialization
- ✅ Sliding window behavior
- ✅ Redis integration (with real Redis)
- ✅ Different keys are independent
- ✅ Reset functionality
- ✅ Graceful degradation on Redis failure
- ✅ IP extraction logic
- ✅ Trusted proxy validation

**Test Count:** 20+ tests

### Integration Tests

**Coverage:**
- ✅ Login endpoint rate limiting
- ✅ Register endpoint rate limiting
- ✅ Rate limit headers in responses
- ✅ Different endpoints have separate limits
- ✅ Concurrent requests from different IPs

**Test Count:** 10+ integration tests

### Missing Test Coverage

❌ **File upload rate limiting** (not implemented)
❌ **Token refresh rate limiting** (not implemented)
❌ **Admin endpoint rate limiting** (not implemented)
❌ **Account lockout edge cases** (partial coverage)
❌ **Token bucket burst behavior** (partial coverage)

**Recommendation:** Add tests for new rate limiting as it's implemented

---

## Compliance Notes

### ACGME Compliance

**Not applicable** - Rate limiting is a security measure, not a clinical compliance requirement.

### HIPAA Compliance

**Indirect benefit:**
- Rate limiting helps prevent brute force attacks on PHI-containing accounts
- Lockout mechanism protects against credential stuffing
- Audit logs should track rate limit violations for security monitoring

**Recommendation:** Ensure rate limit violations are logged to audit system for HIPAA security monitoring requirements.

### OWASP Top 10

**Coverage:**

| OWASP Risk | Mitigation | Status |
|------------|-----------|--------|
| A07:2021 - Identification and Authentication Failures | Account lockout, login rate limiting | ✅ Strong |
| A05:2021 - Security Misconfiguration | Fail-open design, configurable limits | ✅ Good |
| A04:2021 - Insecure Design | Defense in depth, multiple layers | ✅ Strong |

---

## Summary

### Strengths

1. ✅ **Multi-layered defense** - Three independent rate limiting mechanisms
2. ✅ **Account lockout with exponential backoff** - Prevents distributed brute force
3. ✅ **Tiered rate limiting** - Role-based access control for API usage
4. ✅ **Per-endpoint limits** - Protects expensive operations
5. ✅ **Graceful degradation** - System remains available if Redis fails
6. ✅ **Trusted proxy handling** - Prevents header spoofing attacks
7. ✅ **Comprehensive testing** - Good unit and integration test coverage
8. ✅ **Industry-standard algorithms** - Sliding window + token bucket

### Critical Gaps

1. ⚠️ **File upload not rate limited** - Storage/bandwidth exhaustion risk
2. ⚠️ **Token refresh not rate limited** - Token abuse risk

### Priority Action Items

| Priority | Action | Estimated Effort | Impact |
|----------|--------|-----------------|--------|
| 🔴 **CRITICAL** | Add file upload rate limiting | 1-2 hours | High |
| 🟠 **HIGH** | Add token refresh rate limiting | 30 minutes | High |
| 🟡 **MEDIUM** | Add admin endpoint rate limiting | 1 hour | Medium |
| 🟡 **MEDIUM** | Externalize lockout config | 30 minutes | Medium |
| 🟢 **LOW** | Separate internal service key | 15 minutes | Low |

### Overall Assessment

The Residency Scheduler has a **robust and well-designed rate limiting system** that protects against most common attack vectors. The use of multiple independent layers (SlowAPI, custom middleware, account lockout) provides defense-in-depth. The main gaps are in newer features (file uploads) and token management endpoints that were added after the initial rate limiting implementation.

**Recommended Action:** Implement the two critical gaps (file upload and token refresh rate limiting) before the next production deployment. The remaining gaps can be addressed in subsequent sprints as part of ongoing security hardening.

---

**Report Generated:** 2025-12-30
**Next Review Date:** Q1 2026
**Contact:** Security Team
