# Backend Issues That Look Like Frontend Bugs

Purpose: quick map of backend/middleware/routing behaviors that commonly surface as “frontend” issues.

## 1) /api → /api/v1 Redirect (307) Drops CORS Headers

Where:
- `backend/app/main.py:294`

Symptom:
- Browser shows “CORS blocked” even though backend is running.

Cause:
- Redirect response does not include CORS headers. Browser blocks it before retry.

Fix:
- Frontend must use `/api/v1` directly.

## 2) Auth Cookie Not Sent → 401 → Frontend Redirect - PARTIALLY FIXED

Where:
- `backend/app/core/security.py:325` (cookie auth)
- `backend/app/api/routes/auth.py` (login sets cookie)
- `frontend/src/lib/api.ts:167` (401 redirect interceptor)

Symptom:
- User logs in, then gets bounced to `/login` when hitting protected pages.

Cause:
- Cookie not sent (wrong domain, Secure flag over HTTP, missing `withCredentials`, or CORS mismatch).
- **Additional issue found**: 401 interceptor redirected on ALL 401s including `/auth/me` calls during auth check

Fix Applied:
- Frontend uses `withCredentials: true` (verified in `api.ts:132`)
- Updated 401 interceptor to skip redirect for `/auth/` endpoints (`api.ts:168-170`)
- CORS verified working (allow_credentials=true, localhost:3000 allowed)

Status: **CODE FIXED** - needs browser verification (2025-12-22)

## 3) Global Rate Limiting Masks Real Failures

Where:
- `backend/app/main.py:244` (SlowAPI middleware)
- `backend/app/middleware/rate_limit_middleware.py`

Symptom:
- UI flickers or gets stuck in auth loading loops after repeated failures.

Cause:
- 429s block `/auth/me` and other core endpoints, causing the UI to re-render indefinitely.

Fix:
- Disable rate limits in local dev (`RATE_LIMIT_ENABLED: "false"`).
- Flush Redis if needed.

## 4) TrustedHostMiddleware Blocks Requests in Production-like Config

Where:
- `backend/app/main.py:266`

Symptom:
- Requests fail with 400/403 when accessing from different hostnames.

Cause:
- `TRUSTED_HOSTS` configured without matching the actual host header.

Fix:
- Ensure `TRUSTED_HOSTS` includes the local hostname or disable for local dev.

## 5) Metrics Path Confusion (double prefix)

Where:
- `backend/app/api/routes/__init__.py:107`
- `backend/app/api/routes/metrics.py`

Symptom:
- UI or tooling requests `/api/v1/metrics/...` and gets 404.

Cause:
- Router prefix `/metrics` + endpoints defined with `/metrics/...` → `/api/v1/metrics/metrics/...`.

Fix:
- Normalize paths or call the correct endpoint.

## 6) Missing /auth/check Endpoint - FIXED

Where:
- `frontend/src/lib/auth.ts:265` calls `/auth/check`
- No matching backend route.

Symptom:
- UI "auth check" returns false even when logged in.

Fix Applied:
- Updated `frontend/src/lib/auth.ts` to use `/auth/me` instead of `/auth/check`
- The `checkAuth()` function now calls `/auth/me` and transforms the response to `{ authenticated: true, user }`

Status: **FIXED** (2025-12-22)

## 7) Security Headers in Debug vs Prod

Where:
- `backend/app/middleware/security_headers.py:94`

Symptom:
- Behavior differs between local and prod (e.g., HSTS, CSP).

Cause:
- Headers are conditional on `DEBUG`.

Fix:
- Ensure environment flags match the intended deployment profile.

---

If a frontend issue looks weird, check backend logs first and confirm the request path is `/api/v1/...`.
