# CRITICAL: Enable Rate Limiting in Production

## ⚠️ Action Required

**Set RATE_LIMIT_ENABLED=true in production .env file**

## Current Status

Rate limiting is **DISABLED by default** for development convenience.

This **MUST** be enabled in production to prevent:
- **Brute force attacks** on login endpoints
- **DDoS attacks** on API endpoints
- **API abuse** and resource exhaustion
- **Credential stuffing** attacks

## Configuration

Add to production `.env` file:

```bash
# CRITICAL SECURITY: Enable rate limiting
RATE_LIMIT_ENABLED=true

# Optional: Customize rate limits (defaults shown)
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE=5
RATE_LIMIT_BURST_SIZE=10
```

## Default Rate Limits

| Endpoint Type | Default Limit | Configurable Via |
|---------------|---------------|------------------|
| Authentication | 5 req/min | `RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE` |
| General API | 60 req/min | `RATE_LIMIT_REQUESTS_PER_MINUTE` |
| Burst Size | 10 requests | `RATE_LIMIT_BURST_SIZE` |

## Verification

After enabling, verify rate limiting is active:

```bash
# Check application logs for rate limit messages
docker-compose logs backend | grep -i "rate limit"

# Test rate limiting (should return 429 after limit exceeded)
for i in {1..10}; do curl -I http://localhost:8000/api/auth/login; done
```

Expected response when limit exceeded:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

## Implementation Details

Rate limiting is implemented in:
- **File**: `backend/app/core/rate_limit.py`
- **Middleware**: Applied to all API routes
- **Storage**: Redis-backed (requires Redis running)

## Security Impact

| Setting | Risk Level | Impact |
|---------|------------|--------|
| DISABLED (dev default) | 🔴 CRITICAL | Open to brute force, DDoS, abuse |
| ENABLED (production) | 🟢 SECURE | Protected against automated attacks |

## Deployment Checklist

- [ ] Add `RATE_LIMIT_ENABLED=true` to production `.env`
- [ ] Verify Redis is running (`docker-compose ps redis`)
- [ ] Test rate limiting works (see Verification above)
- [ ] Monitor rate limit metrics in logs
- [ ] Consider adjusting limits based on traffic patterns

## Additional Security Measures

While rate limiting is critical, also ensure:
1. Strong password policies enforced
2. Account lockout after repeated failures (see `backend/app/core/security.py`)
3. CAPTCHA on public-facing forms
4. IP-based blocking for persistent attackers
5. Monitoring and alerting for unusual traffic patterns

## References

- [OWASP: Credential Stuffing Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html)
- [OWASP: Denial of Service](https://owasp.org/www-community/attacks/Denial_of_Service)
- Application rate limit configuration: `backend/app/core/rate_limit.py`

---

**Last Updated**: 2025-12-30
**Priority**: CRITICAL
**Required Before**: Production deployment
