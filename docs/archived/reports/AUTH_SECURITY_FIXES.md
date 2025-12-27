# Authentication Security Fixes Summary

**Last Updated:** 2025-12-21
**Related PRs:** #327, #328
**Status:** All fixes implemented and tested

---

## Overview

This document summarizes security fixes applied to the authentication system to address vulnerabilities identified in Codex review of Session 13 PRs.

---

## Vulnerabilities Fixed

### 1. Refresh Token Privilege Escalation (P0 - Critical)

**Severity:** CRITICAL
**Location:** `backend/app/core/security.py:201-254`
**PR:** #327, #328

**Vulnerability:**
Refresh tokens could be used as access tokens because `verify_token()` did not check the token type. Since refresh tokens are long-lived (7 days) while access tokens are short-lived (30 minutes), an attacker who stole a refresh token could use it for API access for the full 7-day lifetime, bypassing the intended 30-minute access window.

**Attack Vector:**
```
1. Attacker steals refresh token (via XSS, MITM, etc.)
2. Attacker uses refresh token in Authorization header: "Bearer <refresh_token>"
3. API accepts it because both tokens are signed with same key and have valid claims
4. Attacker has 7 days of API access instead of needing to use /refresh endpoint
```

**Fix Applied:**
```python
# In verify_token() - security.py:221-226
# SECURITY: Reject refresh tokens - they must only be used at /refresh endpoint
if payload.get("type") == "refresh":
    if obs_metrics:
        obs_metrics.record_auth_failure("refresh_token_as_access")
    return None
```

**Test Coverage:**
- `test_refresh_token_cannot_be_used_as_access_token` - Verifies header-based rejection
- `test_refresh_token_in_cookie_rejected` - Verifies cookie-based rejection

---

### 2. Refresh Token Reuse After Rotation (P1 - High)

**Severity:** HIGH
**Location:** `backend/app/core/security.py:128-198`, `backend/app/api/routes/auth.py:204-282`
**PR:** #327

**Vulnerability:**
When refresh token rotation was enabled, old refresh tokens were not blacklisted after use. An attacker with a stolen refresh token could continue using it indefinitely, even after the legitimate user had rotated their token.

**Attack Vector:**
```
1. Attacker steals refresh token at time T
2. Legitimate user refreshes at T+1 (gets new refresh token)
3. Attacker uses stolen token at T+2 - still works!
4. Both attacker and user now have valid sessions
```

**Fix Applied:**
```python
# In verify_refresh_token() - security.py:176-185
# Blacklist the token after successful verification if requested
if blacklist_on_use and expires_at:
    blacklist_token(
        db=db,
        jti=jti,
        expires_at=expires_at,
        user_id=UUID(user_id) if user_id else None,
        reason="refresh_rotation"
    )

# In /refresh endpoint - auth.py:228-232
token_data, old_jti, old_expires = verify_refresh_token(
    token=request.refresh_token,
    db=db,
    blacklist_on_use=settings.REFRESH_TOKEN_ROTATE,  # Blacklist when rotating
)
```

**Test Coverage:**
- `test_refresh_blacklists_old_token_on_rotation` - Verifies token is blacklisted
- `test_refresh_reused_token_rejected` - Verifies reuse returns 401
- `test_multiple_rapid_refreshes_all_blacklisted` - Verifies chain of rotations

---

### 3. Test Validation Bug (P1 - Test Fix)

**Severity:** MEDIUM (test reliability)
**Location:** `backend/tests/test_auth_routes.py:915-917`
**PR:** #328

**Issue:**
The test `test_refresh_token_cannot_be_used_as_access_token` was passing for the wrong reason. The login endpoint sets an access_token cookie, so when the test tried to use a refresh token in the Authorization header, the `get_current_user` function was authenticating via the leftover cookie instead.

**Fix Applied:**
```python
# Clear cookies so the test actually exercises the Authorization header path
client.cookies.clear()

# Now this request relies solely on the refresh token in the header
response = client.get(
    "/api/auth/me",
    headers={"Authorization": f"Bearer {refresh_token}"}
)
```

---

## Token Security Architecture

### Dual-Token System

| Token Type | Lifetime | Purpose | Storage |
|------------|----------|---------|---------|
| Access Token | 30 min | API authentication | httpOnly cookie |
| Refresh Token | 7 days | Obtain new access tokens | Client-side secure storage |

### Token Claims

**Access Token:**
```json
{
  "sub": "user-uuid",
  "username": "user@example.com",
  "exp": 1703123456,
  "iat": 1703121656,
  "jti": "unique-token-id"
}
```

**Refresh Token:**
```json
{
  "sub": "user-uuid",
  "username": "user@example.com",
  "exp": 1703726456,
  "iat": 1703121656,
  "jti": "unique-token-id",
  "type": "refresh"  // <-- Key differentiator
}
```

### Security Flow

```
Login:
  User → POST /login → Access Token (cookie) + Refresh Token (body)

API Request:
  User → GET /api/resource (cookie sent automatically)
       → verify_token() checks: NOT type="refresh" → Allow

Token Refresh:
  User → POST /refresh (refresh_token in body)
       → verify_refresh_token(blacklist_on_use=true)
       → Old token blacklisted
       → New tokens issued

Logout:
  User → POST /logout
       → Access token blacklisted
       → Cookie deleted
```

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `REFRESH_TOKEN_ROTATE` | true | Enable rotation + blacklisting |

---

## Related Documentation

- **API Documentation:** `docs/api/authentication.md`
- **Security Assessment:** `docs/archived/reports/SECURITY_VULNERABILITY_ASSESSMENT.md`
- **CHANGELOG:** See "Security & Bug Fixes (Session 13)" section

---

## Verification

All security fixes have been verified with passing tests:

```bash
pytest tests/test_auth_routes.py -v -k "refresh"
```

Key tests:
- ✅ `test_refresh_token_cannot_be_used_as_access_token`
- ✅ `test_refresh_token_in_cookie_rejected`
- ✅ `test_refresh_blacklists_old_token_on_rotation`
- ✅ `test_refresh_reused_token_rejected`
- ✅ `test_refresh_new_token_works_after_rotation`
- ✅ `test_multiple_rapid_refreshes_all_blacklisted`
