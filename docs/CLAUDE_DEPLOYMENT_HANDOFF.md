# Claude Deployment Handoff

Purpose: deployment-focused bug list with impact and suggested fixes, plus other notable issues.

## Deployment-Blocking or High-Risk Issues

1) DEBUG defaults to true (production hardening off by default)
- Impact: HSTS and other prod-only protections are disabled unless DEBUG is explicitly set false; easy to deploy insecure defaults.
- Evidence: `backend/app/core/config.py:52`, `backend/app/middleware/security_headers.py:94`
- Suggested fix: default `DEBUG` to false in production config or require explicit env override; fail fast when DEBUG true in non-dev environment.

2) Metrics API path mismatch (double prefix)
- Impact: `/api/v1/metrics/...` is documented but actual paths become `/api/v1/metrics/metrics/...`, breaking monitoring clients and docs; confusion during rollout.
- Evidence: router mounted at `/metrics` in `backend/app/api/routes/__init__.py:107` and endpoints defined as `/metrics/...` in `backend/app/api/routes/metrics.py:25`
- Suggested fix: either mount router at `/` and keep `/metrics/...` endpoints, or keep prefix `/metrics` and change endpoints to `/health`, `/info`, `/export`, `/summary`, `/reset`.

3) OAuth2 tokenUrl mismatch in OpenAPI
- Impact: Swagger “Authorize” and any client generator using OpenAPI will point to `/api/auth/login` while the app serves `/api/v1/auth/login` (via redirect). In production gateways, redirects may be blocked.
- Evidence: `backend/app/core/security.py:30`, `backend/app/main.py:326`
- Suggested fix: update tokenUrl to `/api/v1/auth/login` or compute dynamically from settings/base path.

4) Logout does not blacklist cookie-auth tokens
- Impact: production auth uses httpOnly cookies; logout only checks Authorization header token, leaving cookie token valid until expiry. Users can appear logged out in UI but token remains usable.
- Evidence: `backend/app/api/routes/auth.py:159`, `backend/app/core/security.py:325`
- Suggested fix: extract token from cookies in logout (same logic as `get_current_user`) and blacklist it when present.

5) Refresh token flow unusable with cookie auth
- Impact: backend returns refresh tokens in the response body but never sets a refresh cookie; frontend never stores refresh token, so refresh cannot happen despite docs/comments suggesting cookie-based refresh.
- Evidence: `backend/app/api/routes/auth.py:96`, `frontend/src/lib/auth.ts:109`
- Suggested fix: either set refresh token as httpOnly cookie server-side or return/handle refresh token on client and store it securely; align docs and code.

6) Duplicate cache TTL config keys override each other
- Impact: production caching behavior is ambiguous; later definitions override earlier defaults silently.
- Evidence: `backend/app/core/config.py:80`, `backend/app/core/config.py:115`
- Suggested fix: remove duplicate fields or consolidate into a single set of cache TTLs.

## Additional Non-Deployment Issues (Still Worth Fixing)

1) Missing `/auth/check` endpoint
- Impact: frontend `checkAuth()` always returns `authenticated: false`, breaking auth guards or login flows.
- Evidence: `frontend/src/lib/auth.ts:243`, no route in `backend/app/api/routes/auth.py`
- Suggested fix: add `/auth/check` endpoint or update frontend to use `/auth/me` with proper error handling.

2) Metrics docstrings and examples reference `/api/v1/metrics/...` while router prefixes cause `/api/v1/metrics/metrics/...`
- Impact: API docs and client expectations are inconsistent even outside deployment contexts.
- Evidence: `backend/app/api/routes/metrics.py:37`
- Suggested fix: align docs after correcting router paths.
