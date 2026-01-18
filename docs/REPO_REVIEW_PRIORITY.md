# Repo Review Priority List (2026-01-16)

Scope: fast scan of backend, mcp-server, frontend, configs, and tests. Emphasis on auth, data exposure, and deployment safety.

## P0 Critical
- GraphQL API is mounted without auth or authorization. Queries are fully unauthenticated and mutations only check for a user object, so any authenticated user can create/update/delete core records without role checks. `backend/app/main.py:428` `backend/app/graphql/schema.py:23` `backend/app/graphql/resolvers/queries.py:35` `backend/app/graphql/resolvers/mutations.py:27`
- GraphQL subscriptions allow anonymous access and ignore user context for filtering. Any subscriber can receive schedule/swap/conflict updates for any user when filters are omitted or spoofed. `backend/app/graphql/subscriptions.py:331` `backend/app/graphql/subscriptions.py:505`
- Default admin user is auto-created on empty DB with static credentials `admin` / `admin123` and no DEBUG gating. This is a production foot-gun if a fresh DB is exposed. `backend/app/main.py:108`
- MCP HTTP auth bypass: APIKeyAuthMiddleware exempts `/` while the MCP app is also mounted at `/`. This creates an unauthenticated entry point even when `MCP_API_KEY` is set. `mcp-server/src/scheduler_mcp/server.py:5340`
- MCP HTTP auth fails open when `MCP_API_KEY` is unset, leaving tool execution unauthenticated. `mcp-server/src/scheduler_mcp/server.py:5354`
- Constraint management endpoints (enable/disable/preset) are unauthenticated, allowing anyone to weaken or disable scheduling constraints. `backend/app/api/routes/constraints.py:88`

## P1 High
- `.env` contains real secrets and default admin credentials; if shared or accidentally committed, it leaks DB, Redis, and webhook secrets. Ensure secrets are rotated and never leave the workstation. `.env:9` `.env:14` `.env:43`
- DEBUG defaults to true; combined with `.env` this disables secure cookies and HSTS and keeps dev-only behavior on by default. `backend/app/core/config.py:53` `.env:21`
- GraphiQL is always enabled for GraphQL; in production this expands the attack surface and encourages unauthenticated probing. `backend/app/graphql/schema.py:68`
- GraphQL context uses `verify_token` without active-user checks, so deactivated accounts remain valid until token expiry. `backend/app/graphql/schema.py:57` `backend/app/core/security.py:204`
- Scheduler ops and queue management endpoints allow any authenticated user to submit/cancel jobs, generate approval tokens, or abort solver runs; the queue submit path accepts arbitrary Celery task names, which is a privilege escalation risk. `backend/app/api/routes/scheduler_ops.py:625` `backend/app/api/routes/queue.py:40` `backend/app/queue/manager.py:38` `backend/app/api/routes/jobs.py:40`
- MCP server fallback path (SSE) skips API key enforcement entirely if advanced HTTP features are unavailable, even when `MCP_API_KEY` is set. `mcp-server/src/scheduler_mcp/server.py:5508`
- Fatigue Risk endpoints expose resident fatigue profiles and allow assessments without auth; this likely leaks PHI/PII. `backend/app/api/routes/fatigue_risk.py:24`

## P2 Medium
- Health endpoints expose detailed dependency and DB metadata without auth, including `/health/detailed` and service-specific checks. Consider restricting in production. `backend/app/api/routes/health.py:96`
- Metrics endpoints under `/api/v1/metrics` have no auth, exposing internal metric names and system stats. `backend/app/api/routes/metrics.py:21`
- Documentation endpoints under `/api/v1/docs` expose enriched OpenAPI and examples without auth, even when built-in docs are disabled. `backend/app/api/routes/docs.py:17`
- Changelog endpoints under `/api/v1/changelog` allow unauthenticated schema uploads and version writes to `/tmp`, which is likely unintended for production. `backend/app/api/routes/changelog.py:31`
- Credential lookup endpoints (list/summary/qualified-faculty) lack authentication, exposing faculty credential status publicly. `backend/app/api/routes/credentials.py:20`
- FMIT health and fairness analytics endpoints are unauthenticated, exposing coverage, alert, and workload data. `backend/app/api/routes/fmit_health.py:14` `backend/app/api/routes/fairness.py:11`
- Exotic resilience endpoints are unauthenticated, likely exposing schedule analytics derived from assignments. `backend/app/api/routes/exotic_resilience.py:31`
- Generic XLSX parse endpoint allows unauthenticated file uploads; validate DoS and abuse risk. `backend/app/api/routes/imports.py:20`
- Scheduler ops approval tokens do not enforce expiration or one-time use, so old tokens can be replayed. `backend/app/api/routes/scheduler_ops.py:808`
- `/metrics` is protected by client IP only; behind proxies this can allow unintended external access if proxy IPs are trusted implicitly. `backend/app/main.py:407`
- Repo root contains large XLSX/XML/PDF exports that likely include schedule data; validate for PHI/PII and keep them out of version control. `Block10_*.xlsx` `Block10_*.xml` `tan_2026_oi_251437_1767812642.93194.pdf`

## Test Gaps
- Security tests are explicitly skipped for brute-force, lockout, CSRF, and password complexity. These are acknowledged gaps and should be closed or removed once controls exist. `backend/tests/security/test_security_features.py:52`
- Multiple frontend resilience feature tests are skipped due to unimplemented components, which masks regressions in the resilience UI. `frontend/__tests__/features/resilience/contingency-analysis.test.tsx:33`

## P3 Low
- Claude chat WebSocket auth is broken: `get_user_from_token` is referenced but not implemented, and role checks compare uppercase strings against lower-case roles, blocking legitimate users. `backend/app/api/deps.py:19` `backend/app/api/routes/claude_chat.py:685`

## Suggested Claude Work Order
1. Lock down GraphQL: require auth, add role/tenant checks, and disable GraphiQL outside DEBUG.
2. Remove or gate default admin bootstrap in production.
3. Fix MCP auth: remove `/` exemption or stop mounting MCP at `/`, and require `MCP_API_KEY` unless explicit dev flag is set.
4. Restrict health and metrics endpoints in production.
5. Audit repo data artifacts and remove or sanitize PHI/PII exports.
