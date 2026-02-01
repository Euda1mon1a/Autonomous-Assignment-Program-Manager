# MCP Production Security Checklist

Purpose: Ensure the MCP server is locked down for production deployments (no unauthenticated access, no public exposure).

## 1) Required Environment Variables

- `MCP_API_KEY` set to a strong secret (32+ chars).
  - Generate: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`
- `MCP_ALLOW_LOCAL_DEV` **NOT** set (or explicitly `false`).
- `MCP_TRANSPORT=http` (preferred for production; supports API key auth).
- `API_USERNAME` / `API_PASSWORD` set for MCP → backend API access.

## 2) Network Exposure Controls

- MCP HTTP ports are **not** exposed to the public internet.
- If running via Docker, bind to localhost only:
  - `127.0.0.1:8080:8080` (see `docker-compose.yml` in this repo).
- If using a reverse proxy, require auth and forward `Authorization` header.

## 3) Authentication Enforcement (HTTP Transport)

Expected behavior from `mcp-server/src/scheduler_mcp/server.py`:
- Only `/health` is exempt from auth.
- All other paths require `Authorization: Bearer <MCP_API_KEY>` (or raw token).
- If `MCP_API_KEY` is missing and request is non-local, server **fails closed**.

Verification (on the MCP host):
- `curl -s http://127.0.0.1:8080/health` -> 200 OK
- `curl -s http://127.0.0.1:8080/mcp` -> 401 Unauthorized (when no header)
- `curl -s -H "Authorization: Bearer $MCP_API_KEY" http://127.0.0.1:8080/mcp` -> 200 OK

## 4) SSE Fallback (Do Not Use in Production)

The SSE fallback does **not** support API key auth. Production should use HTTP transport.
- If SSE is used on non-localhost without `MCP_API_KEY`, the server raises a runtime error.
- If SSE is used on localhost, it will run **without** auth (dev only).

## 5) Log Signals (Required)

On startup, logs should include:
- `API key authentication enabled`
- No warnings about running without authentication.

## 6) Checklist Verification Summary

Mark each item during production rollout:
- [ ] `MCP_API_KEY` set (32+ chars)
- [ ] `MCP_ALLOW_LOCAL_DEV` unset/false
- [ ] MCP HTTP port bound to localhost or internal network only
- [ ] Reverse proxy (if used) forwards `Authorization` header
- [ ] `/health` OK, `/mcp` requires API key
- [ ] Logs show auth enabled, no insecure warnings
