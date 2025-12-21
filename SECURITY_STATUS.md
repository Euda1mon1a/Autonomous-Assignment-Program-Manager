# Security Vulnerability Status

**Last Updated:** 2025-12-21 (10 security fixes in parallel batch)
**Original Assessment:** 2025-12-17

This document tracks security vulnerabilities identified in the codebase and their remediation status.

---

## Summary

| Severity | Total | Fixed | Open |
|----------|-------|-------|------|
| CRITICAL | 8 | 8 | 0 |
| HIGH | 8 | 8 | 0 |
| MEDIUM | 15 | 11 | 4 |
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

### 5. ~~glob CLI Command Injection (GHSA-5j98-mcp5-4vw2)~~
- **Status:** FIXED
- **Fixed In:** `frontend/package.json` (npm overrides)
- **Severity:** High (development dependency)
- **Details:**
  - Vulnerability in glob 10.2.0-10.4.5 allowed command injection via `-c/--cmd` flag
  - Fixed by adding npm `overrides` to pin glob to ^10.5.0
  - **Why NOT `npm audit fix --force`:** Upgrades eslint-config-next v14→v16, which requires ESLint v9 and breaks `next lint` with Next.js 14
  - See `docs/operations/VALIDATION_TRACKER.md` for full history

### 6. ~~Refresh Token Usable as Access Token~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/security.py:201-226` (PR #327)
- **Severity:** High (privilege escalation)
- **Details:**
  - **Vulnerability:** Refresh tokens (7-day lifetime) could be used as access tokens (30-min lifetime)
  - `verify_token()` did not check token type, accepting any valid JWT
  - Attackers could use stolen refresh tokens directly in Authorization header for 7 days
  - **Fix:** `verify_token()` now explicitly rejects tokens with `type="refresh"`
  - Refresh tokens can only be used at the `/api/auth/refresh` endpoint
  - Added tests: `test_refresh_token_cannot_be_used_as_access_token`, `test_refresh_token_in_cookie_rejected`

### 7. ~~24-Hour Token Expiration Without Refresh~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/config.py:55`, documentation files
- **Details:**
  - Reduced ACCESS_TOKEN_EXPIRE_MINUTES from 1440 (24 hours) to 15 minutes
  - 96x reduction in token theft exposure window
  - Refresh token rotation already implemented with proper blacklisting
  - Updated all documentation to reflect new 15-minute default

### 8. ~~No Per-User Account Lockout~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/rate_limit.py:346-543`, `backend/app/controllers/auth_controller.py`
- **Details:**
  - Added `AccountLockout` class with exponential backoff
  - Locks account after 5 failed attempts
  - Initial lockout: 60 seconds, doubles with each subsequent failure (max 1 hour)
  - Complements IP-based rate limiting to prevent distributed brute force attacks
  - Lockout cleared on successful login
  - Note: This is independent of token handling - only tracks failed authentication attempts

---

## Medium Vulnerabilities

### 1. ~~CORS Overly Permissive~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/config.py`, `backend/app/main.py`
- **Details:**
  - Added `validate_cors_origins()` validator with production enforcement
  - Forbids wildcard "*" in production (DEBUG=False), raises ValueError
  - Added `CORS_ORIGINS_REGEX` for flexible subdomain matching
  - 6 new test cases added, all passing

### 2. CSP Allows unsafe-inline/unsafe-eval
- **Location:** Next.js configuration
- **Status:** OPEN - Required for Next.js but weakens XSS protection

### 3. ~~Missing Startup Secret Validation for All Services~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/config.py:13-43, 147-304`
- **Details:**
  - Added comprehensive weak password list (WEAK_PASSWORDS) including common defaults and .env.example placeholders
  - **SECRET_KEY & WEBHOOK_SECRET:** Enhanced validators now check against weak password list and minimum length (32 chars)
  - **REDIS_PASSWORD:** New validator requires non-empty strong password in production (min 16 chars), allows empty in debug mode
  - **DATABASE_URL:** New validator extracts and validates password from connection string (min 12 chars)
  - All validators use DEBUG flag: errors in production (DEBUG=False), warnings in development (DEBUG=True)
  - Application fails fast at startup if production secrets are weak/default
  - Added comprehensive test coverage in `tests/test_core.py::TestSecretValidation`

### 4. ~~Date Parsing Without Business Logic Validation~~
- **Status:** FIXED
- **Fixed In:** `backend/app/validators/date_validators.py`, 8 schema files
- **Details:**
  - Created reusable date validators with reasonable bounds (2020-2050)
  - Updated 8 Pydantic schemas: block, schedule, leave, absence, certification, procedure_credential, swap, academic_blocks
  - Validates date order (start < end) and expiration logic
  - 21 test cases added, all passing

### 5. ~~Potential Email Regex ReDoS~~
- **Status:** FIXED
- **Fixed In:** `backend/tests/test_notifications.py`
- **Details:**
  - Production code already used Pydantic's `EmailStr` with email-validator library
  - Removed custom regex from test file, replaced with email-validator library
  - No custom email regex patterns remain in codebase

### 6. ~~Long Token Expiration Without Refresh~~
- **Status:** FIXED (See High #7)
- **Details:** Access token lifetime reduced to 15 minutes, refresh token rotation implemented

### 7. No Multi-Factor Authentication
- **Status:** OPEN - Add TOTP for admin accounts

### 8. ~~Monitoring Services Exposed~~
- **Status:** FIXED
- **Fixed In:** `monitoring/docker-compose.monitoring.prod.yml` (new), `monitoring/DEPLOYMENT.md` (new)
- **Details:**
  - Created production override file that removes ALL external port mappings (9 services)
  - Development ports preserved for convenience (clearly labeled dev-only)
  - Production deployment: `docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml up -d`
  - Added comprehensive deployment guide with secure access methods (reverse proxy, SSH tunnel, VPN)

### 9. ~~Database Connection String Weak Default~~
- **Status:** FIXED (See #3 - Startup Secret Validation)
- **Details:** DATABASE_URL password now validated (min 12 chars, rejects "scheduler" default)

### 10. ~~No Request ID Tracking~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/observability.py`, `backend/tests/test_request_id_middleware.py` (new)
- **Details:**
  - RequestIDMiddleware already existed, enhanced with security validation
  - Added length validation (max 255 chars), whitespace handling
  - X-Request-ID in response headers, stored in context for logging
  - 21 comprehensive test cases added, all passing

### 11. ~~Webhook Secret Has Dev Default~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/config.py:147-189`, `.env.example:23-26`
- **Details:**
  - WEBHOOK_SECRET now validated using same pattern as SECRET_KEY
  - Rejects weak/default values and secrets < 32 characters in production
  - Logs warnings in development mode (DEBUG=True) but allows weak secrets
  - Raises errors in production mode (DEBUG=False) to prevent startup
  - Added to `.env.example` with generation instructions

### 12. ~~Table Name Interpolation in Audit Queries~~
- **Status:** FIXED
- **Fixed In:** `backend/app/repositories/audit_repository.py`, `backend/app/services/audit_service.py`
- **Details:**
  - Added `_validate_and_quote_table_name()` with allowlist validation
  - PostgreSQL double-quotes applied to all dynamic table names
  - 5 SQL queries updated with defense-in-depth (allowlist + quoting)

### 13. ~~Missing Content-Type Validation on Some Uploads~~
- **Status:** FIXED
- **Fixed In:** `backend/app/core/file_security.py`, `backend/app/api/routes/schedule.py`
- **Details:**
  - Added three-way cross-validation: Extension + Content-Type Header + Magic Bytes
  - Uses python-magic (already in requirements.txt) for MIME detection
  - Updated 4 file upload endpoints to pass content_type
  - 13 test cases added covering spoofing attacks

### 14. No Password History/Rotation
- **Status:** OPEN - Implement password policies

### 15. ~~cAdvisor Running Privileged~~
- **Status:** FIXED
- **Fixed In:** `monitoring/docker-compose.monitoring.yml:147-175`
- **Details:**
  - Replaced `privileged: true` with specific capabilities (SYS_PTRACE, DAC_READ_SEARCH)
  - Added `cap_drop: ALL` to drop all capabilities first
  - Added `security_opt: no-new-privileges:true` to prevent privilege escalation
  - Added `--docker_only=true` flag to reduce attack surface

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

- [x] All HIGH vulnerabilities are addressed
- [x] `.env` file has strong, unique values for all secrets (startup validation enforces this)
- [ ] `TRUSTED_PROXIES` configured if behind load balancer
- [x] Monitoring services moved to internal network (use docker-compose.monitoring.prod.yml)
- [x] Redis password is not using dev default (startup validation enforces this)
- [x] CORS origins restricted to production domains (wildcard rejected in production)
- [ ] API documentation disabled (`/docs`, `/redoc`)
- [ ] Penetration testing completed

---

## References

- Original Assessment: `docs/archived/reports/SECURITY_VULNERABILITY_ASSESSMENT.md`
- OWASP Top 10: https://owasp.org/Top10/
- NIST Password Guidelines: https://pages.nist.gov/800-63-3/
