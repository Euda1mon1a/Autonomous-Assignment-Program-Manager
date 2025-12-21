# Security Vulnerability Status

**Last Updated:** 2025-12-21
**Original Assessment:** 2025-12-17

This document tracks security vulnerabilities identified in the codebase and their remediation status.

---

## Summary

| Severity | Total | Fixed | Open |
|----------|-------|-------|------|
| CRITICAL | 8 | 8 | 0 |
| HIGH | 6 | 4 | 2 |
| MEDIUM | 15 | 1 | 14 |
| LOW | 5 | 0 | 5 |

---

## Critical Vulnerabilities (All Fixed)

### 1. ~~Path Traversal in Backup/Restore Operations~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/file_security.py`
- **Details:** Added `validate_backup_id()` and `validate_file_path()` functions. Both `backup.py` and `restore.py` now validate all user-supplied paths.

### 2. ~~Default SECRET_KEY~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/config.py:54`
- **Details:** Uses `secrets.token_urlsafe(64)` as default with validator requiring 32+ characters. Rejects known insecure defaults.

### 3. ~~Default N8N Password~~
- **Status:** FIXED
- **Fixed In:** `docker-compose.yml:153`
- **Details:** Removed default value. Now requires `${N8N_PASSWORD}` to be set in `.env`.

### 4. ~~Default Grafana Password~~
- **Status:** FIXED
- **Fixed In:** `monitoring/docker-compose.monitoring.yml:70`
- **Details:** Removed default value. Now requires `${GRAFANA_ADMIN_PASSWORD}` to be set.

### 5. ~~Token Storage in localStorage (XSS Vulnerable)~~
- **Status:** FIXED
- **Fixed In:** `frontend/src/lib/auth.ts`
- **Details:** Migrated to httpOnly cookies. Uses `withCredentials: true` for all auth requests.

### 6. ~~Unrestricted File Upload~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/file_security.py`
- **Details:** Added comprehensive validation:
  - File size limit (10MB max)
  - Extension whitelist (`.xlsx`, `.xls` only)
  - Magic byte verification (content-type spoofing prevention)
  - Filename sanitization

### 7. ~~XSS in PDF Export~~
- **Status:** FIXED
- **Fixed In:** `frontend/src/features/audit/AuditLogExport.tsx:107-115`
- **Details:** Added `escapeHTML()` function applied to all user-generated content in PDF generation.

### 8. ~~Admin Endpoint Missing Authorization~~
- **Status:** FIXED
- **Fixed In:** `backend/app/api/routes/certifications.py:213`
- **Details:** Added `Depends(require_admin())` to `/admin/send-reminders` endpoint.

---

## High Vulnerabilities

### 1. ~~Rate Limit Bypass via X-Forwarded-For~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/rate_limit.py:260-265`
- **Details:** Now validates that direct client IP is from a trusted proxy before trusting X-Forwarded-For header. Configurable via `TRUSTED_PROXIES` setting.

### 2. ~~Redis Exposed Without Authentication~~
- **Status:** FIXED
- **Fixed In:** `docker-compose.yml:30-32`
- **Details:**
  - Port no longer exposed to host (internal network only)
  - Uses `--requirepass ${REDIS_PASSWORD}`
  - Note: Has dev fallback `:-dev_only_password` - ensure `.env` is configured for production

### 3. ~~Weak Password Validation~~
- **Status:** FIXED
- **Fixed In:** `frontend/src/lib/validation.ts:168-197`
- **Details:** Now enforces:
  - Minimum 12 characters
  - Maximum 128 characters
  - At least 3 of: lowercase, uppercase, numbers, special characters
  - Common password blocklist

### 4. ~~Prometheus Admin API Enabled~~
- **Status:** FIXED
- **Fixed In:** `monitoring/docker-compose.monitoring.yml`
- **Details:** Only `--web.enable-lifecycle` is set, `--web.enable-admin-api` is not enabled.

### 5. 24-Hour Token Expiration Without Refresh
- **Status:** OPEN
- **Location:** `backend/app/core/config.py:55`
- **Risk:** Long-lived tokens increase window for token theft
- **Remediation:** Implement refresh token rotation with shorter access token lifetime (15-30 min)

### 6. No Per-User Account Lockout
- **Status:** OPEN
- **Location:** `backend/app/core/rate_limit.py`
- **Risk:** Distributed brute force attacks can bypass IP-based rate limiting
- **Remediation:** Add user-based lockout after N failed attempts with exponential backoff

---

## Medium Vulnerabilities (Open)

### 1. CORS Overly Permissive
- **Location:** `backend/app/core/config.py`
- **Status:** OPEN - Needs production review

### 2. CSP Allows unsafe-inline/unsafe-eval
- **Location:** Next.js configuration
- **Status:** OPEN - Required for Next.js but weakens XSS protection

### 3. Missing Startup Secret Validation for All Services
- **Status:** OPEN - SECRET_KEY validated, but other secrets need checks

### 4. Date Parsing Without Business Logic Validation
- **Status:** OPEN - Add reasonable date range checks

### 5. Potential Email Regex ReDoS
- **Status:** OPEN - Consider using validated email library

### 6. Long Token Expiration Without Refresh
- **Status:** OPEN - See High #5

### 7. No Multi-Factor Authentication
- **Status:** OPEN - Add TOTP for admin accounts

### 8. Monitoring Services Exposed
- **Status:** OPEN - Prometheus, Grafana ports exposed; move to internal network for production

### 9. Database Connection String Weak Default
- **Status:** OPEN - Requires strong passwords in production

### 10. No Request ID Tracking
- **Status:** OPEN - Add correlation IDs for tracing

### 11. Webhook Secret Has Dev Default
- **Status:** OPEN - Similar to SECRET_KEY, needs production validation

### 12. Table Name Interpolation in Audit Queries
- **Status:** OPEN - Use identifier quoting

### 13. Missing Content-Type Validation on Some Uploads
- **Status:** OPEN - Verify MIME types match extensions

### 14. No Password History/Rotation
- **Status:** OPEN - Implement password policies

### 15. cAdvisor Running Privileged
- **Location:** `monitoring/docker-compose.monitoring.yml:152`
- **Status:** OPEN - Use specific capabilities instead of full privileged mode

---

## Low Vulnerabilities (Open)

### 1. Username Enumeration via Timing
- **Status:** OPEN - Use constant-time comparison

### 2. Rate Limit Headers Expose Capacity
- **Status:** OPEN - Acceptable but monitor

### 3. PGY Validation Inconsistency
- **Status:** OPEN - Align frontend/backend rules

### 4. No Deprecation Headers
- **Status:** OPEN - Add Sunset header for API versioning

### 5. Test Credentials Visible
- **Status:** OPEN - Acceptable for testing but document

---

## Positive Security Findings

The following security measures are properly implemented:

- Bcrypt password hashing with proper salt
- SQLAlchemy ORM preventing SQL injection
- Pydantic validation for type-safe input handling
- Dual-layer rate limiting (Nginx + application)
- Comprehensive security headers (HSTS, CSP, X-Frame-Options)
- Docker secrets support for production
- Non-root containers in all Dockerfiles
- Modern TLS configuration (TLS 1.2/1.3 only)
- JWT blacklist support for token revocation
- Role-based access control (8 user roles)
- Audit logging with version history
- Health checks on all services

---

## Pre-Production Checklist

Before deploying to production, ensure:

- [ ] All HIGH vulnerabilities are addressed
- [ ] `.env` file has strong, unique values for all secrets
- [ ] `TRUSTED_PROXIES` configured if behind load balancer
- [ ] Monitoring services moved to internal network
- [ ] Redis password is not using dev default
- [ ] CORS origins restricted to production domains
- [ ] API documentation disabled (`/docs`, `/redoc`)
- [ ] Penetration testing completed

---

## References

- Original Assessment: `docs/archived/reports/SECURITY_VULNERABILITY_ASSESSMENT.md`
- OWASP Top 10: https://owasp.org/Top10/
- NIST Password Guidelines: https://pages.nist.gov/800-63-3/
