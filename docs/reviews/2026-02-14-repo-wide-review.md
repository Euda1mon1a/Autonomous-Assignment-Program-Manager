# Repo-Wide Review Findings (2026-02-14)

## Scope
- Reviewed code under `backend/`, `frontend/`, `mcp-server/`, and `scripts/`.
- Focused on bug risk, security exposure, behavioral regression risk, and guardrail alignment.
- Methods: targeted static scans plus manual verification of high-signal hits.

## Overall Verdict
- `NEEDS CHANGES`

## Findings

### 1) CRITICAL: Unauthenticated admin bootstrap uses fixed credentials
- Evidence:
- `backend/app/api/routes/auth.py:367` defines `POST /initialize-admin` with no auth dependency.
- `backend/app/api/routes/auth.py:416` creates admin user with fixed password `admin123`.
- `backend/app/api/routes/auth.py:437` returns raw exception text to clients on failure.
- `backend/tests/test_auth_initialization.py:63` explicitly asserts no auth is required.
- `backend/tests/test_auth_initialization.py:43` asserts default password `admin123` is valid.
- Impact:
- If DB is empty in any reachable environment, unauthenticated callers can mint an admin account with known credentials.
- The test suite currently locks this behavior in as expected.
- Recommendation:
1. Gate this endpoint behind `DEBUG` + explicit bootstrap secret (or remove endpoint entirely in favor of CLI-only creation).
2. Eliminate static default passwords; require one-time randomized bootstrap credentials.
3. Replace client-facing `str(e)` with generic errors.
4. Update tests to assert endpoint is disabled/forbidden in non-debug contexts.

### 2) CRITICAL: Internal exception details are exposed broadly to clients
- Evidence:
- Verified pattern `detail=str(e)` / `detail=f"...{str(e)}"` appears `117` times across `33` route/controller files.
- Representative examples:
- `backend/app/api/routes/search.py:76`
- `backend/app/api/routes/rotation_templates.py:189`
- `backend/app/api/routes/queue.py:201`
- `backend/app/api/routes/webhooks.py:82`
- `backend/app/controllers/person_controller.py:146`
- `backend/app/api/routes/claude_chat.py:679` (WebSocket error payload)
- Impact:
- Discloses internal validation, SQL/service internals, and implementation details to clients.
- Increases attack surface and violates client-safe error handling standards.
- Recommendation:
1. Standardize route/controller error translation to client-safe messages.
2. Preserve detailed errors only in server logs with correlation IDs.
3. Add an automated check that rejects new `detail=str(e)` patterns.

### 3) HIGH: Duplicate router registration at multiple prefixes
- Evidence:
- `backend/app/api/routes/__init__.py:146` registers `constraints.router` at `/schedule/constraints`.
- `backend/app/api/routes/__init__.py:209` registers `constraints.router` again at `/constraints`.
- `backend/app/api/routes/__init__.py:149` registers `metrics.router` at `/schedule/metrics`.
- `backend/app/api/routes/__init__.py:267` registers `metrics.router` again at `/metrics`.
- Impact:
- Creates alias sprawl and API contract ambiguity.
- Increases maintenance cost and risks behavior drift between paths (middleware, auth expectations, docs, client generation).
- Recommendation:
1. Choose one canonical prefix per router.
2. If backward compatibility is required, add explicit redirect/compat endpoints with deprecation metadata instead of mounting full routers twice.

### 4) MEDIUM: Hardcoded privileged credentials in operational scripts
- Evidence:
- `scripts/seed_people.py:12` defaults `SEED_ADMIN_PASSWORD` to `admin123`.
- `scripts/seed_templates.py:254` hardcodes `"AdminPassword123!"` for login.
- `scripts/seed_people.py:24` prints a token prefix to stdout.
- Impact:
- Encourages insecure defaults in shared/staging environments.
- Risks accidental credential leakage in logs/terminal history.
- Recommendation:
1. Require credentials via environment variables with no insecure defaults.
2. Fail fast if creds are missing.
3. Remove token logging.

### 5) MEDIUM: Backend contract-normalization logic accepts mixed naming conventions
- Evidence:
- `backend/app/api/routes/backup.py:29` explicitly accepts both snake_case and camelCase table identifiers.
- `backend/app/api/routes/backup.py:32` through `backend/app/api/routes/backup.py:47` maintains dual-format allowlist.
- Impact:
- Blurs API contract boundaries and pushes normalization complexity into backend route layer.
- Increases long-term drift risk versus canonical client interceptor approach.
- Recommendation:
1. Enforce one canonical request contract at API boundary.
2. Keep naming conversion in a single client layer (or a dedicated compatibility adapter with sunset timeline).

### 6) CHECK: Circuit-breaker fallback can mask upstream failures by design
- Evidence:
- `backend/app/resilience/circuit_breaker/breaker.py:135` and `backend/app/resilience/circuit_breaker/breaker.py:138` return fallback when circuit is open.
- `backend/app/resilience/circuit_breaker/breaker.py:185` through `backend/app/resilience/circuit_breaker/breaker.py:190` return fallback after exception.
- Async equivalents at `backend/app/resilience/circuit_breaker/breaker.py:227` and `backend/app/resilience/circuit_breaker/breaker.py:277`.
- Impact:
- Useful for resilience, but can hide true failure modes unless callers/telemetry explicitly surface fallback paths.
- Recommendation:
1. Ensure fallback responses are explicitly marked in return metadata.
2. Emit high-signal telemetry whenever fallback path is used.
3. Confirm callers treat fallback as degraded, not normal success.

## Testing Gaps
- No tests assert that `initialize-admin` is blocked in non-debug production mode.
- Existing tests reinforce insecure behavior (`no_auth_required`, fixed password usage).
- No visible guard test preventing `detail=str(e)` regressions in route/controller layers.

## Guardrail Checks I Did Not Find Violated
- No hits for `extra="allow"` / `ConfigDict(extra="allow")` in scanned source paths.
- Secret length constraints for `SECRET_KEY` and `WEBHOOK_SECRET` are present:
- `backend/app/core/config.py:294`
- `backend/app/config/validator.py:152`
