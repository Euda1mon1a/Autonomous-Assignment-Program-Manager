# MCP Transport Configuration & Security Guide

> **Updated:** 2026-01-03
> **Purpose:** Configure MCP HTTP transport for security and multi-agent concurrency

---

## Table of Contents

1. [Transport Overview](#transport-overview)
2. [Secure HTTP Configuration](#secure-http-configuration)
3. [Configuration Examples](#configuration-examples)
4. [Security Checklist](#security-checklist)
5. [Troubleshooting](#troubleshooting)

---

## Transport Overview

MCP (Model Context Protocol) uses HTTP transport for all deployments:

| Transport | Use Case | Concurrency | Security |
|-----------|----------|-------------|----------|
| **HTTP** | All deployments | Many clients | Requires configuration |

### Architecture

```
HTTP Transport:
Claude Code Session A ──┐
Claude Code Session B ──┼──(HTTP)──> MCP Server (port 8080)
Spawned Agent C ────────┘
```

**Source:** [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)

HTTP transport enables:
- Multi-agent workflows with spawned agents
- Parallel MCP tool calls
- IDE integration (VSCode, Cursor, Zed)
- Multiple developers sharing one MCP server

---

## Secure HTTP Configuration

### Security Threat Model

| Threat | Mitigation |
|--------|------------|
| Network exposure | Bind to `127.0.0.1` only |
| DNS rebinding attacks | Host header validation |
| Unauthorized access | Localhost-only = no auth needed |
| Cross-origin requests | CORS allowlist |

### Secure Configuration

#### 1. Docker Compose (`docker-compose.yml`)

```yaml
mcp-server:
  build:
    context: ./mcp-server
  ports:
    # CRITICAL: Bind to localhost ONLY - not 0.0.0.0
    - "127.0.0.1:8080:8080"
  environment:
    - MCP_TRANSPORT=http
    - MCP_HOST=0.0.0.0           # Inside container, bind all interfaces
    - MCP_PORT=8080
    - MCP_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
    - API_BASE_URL=http://backend:8000
  depends_on:
    backend:
      condition: service_healthy
```

**Why `127.0.0.1:8080:8080`?**

```yaml
# INSECURE - exposes to all network interfaces
ports:
  - "8080:8080"           # Equivalent to 0.0.0.0:8080:8080

# SECURE - localhost only
ports:
  - "127.0.0.1:8080:8080" # Only your machine can reach it
```

#### 2. MCP Configuration (`.mcp.json`)

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://127.0.0.1:8080/mcp",
      "type": "http"
    }
  }
}
```

---

## Configuration Examples

### Development (Local)

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://127.0.0.1:8080/mcp",
      "type": "http"
    }
  }
}
```

### Team Development (Shared Server)

Each developer connects to shared HTTP endpoint:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://dev-server.internal:8080/mcp",
      "type": "http",
      "headers": {
        "Authorization": "Bearer ${MCP_API_KEY}"
      }
    }
  }
}
```

### Production

Use HTTPS with authentication:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "https://mcp.residency-scheduler.internal/mcp",
      "type": "http",
      "headers": {
        "Authorization": "Bearer ${MCP_API_KEY}"
      }
    }
  }
}
```

---

## Security Checklist

### Localhost HTTP (Development)

- [ ] Port bound to `127.0.0.1` not `0.0.0.0`
- [ ] Docker port mapping includes IP: `127.0.0.1:8080:8080`
- [ ] No authentication needed (localhost is trusted)
- [ ] Host header validation enabled in MCP server
- [ ] CORS restricted to localhost origins

### Remote HTTP (Production)

- [ ] HTTPS enabled with valid TLS certificate
- [ ] OAuth 2.1 or API key authentication required
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Network ACLs restrict access
- [ ] DNS rebinding protection enabled
- [ ] CORS configured for specific origins only

### Never Do

- [ ] Expose `0.0.0.0:8080` without authentication
- [ ] Use HTTP (not HTTPS) over network
- [ ] Disable host header validation
- [ ] Allow `*` CORS origins
- [ ] Log authentication tokens

---

## Troubleshooting

### "Connection refused" on HTTP

**Cause:** MCP server not running or wrong port

**Fix:**
```bash
# Check if server is listening
curl -s http://127.0.0.1:8080/health

# Check Docker port mapping
docker compose ps

# Restart MCP server
docker compose restart mcp-server
```

### Agents Still Can't Access MCP Tools

**Cause:** Spawned agents don't inherit MCP tool bindings (Claude Code limitation)

**Workarounds:**
1. Agents use Bash to call MCP via `docker compose exec`
2. Agents call backend API directly instead of MCP
3. Use `MCP_ORCHESTRATION` skill which wraps MCP access
4. Keep MCP-heavy work in main session

### DNS Rebinding Warning

**Cause:** Host header validation not configured

**Fix:** Ensure MCP server validates Host header:
```python
# In MCP server startup
from mcp.server.http import hostHeaderValidation

app.add_middleware(hostHeaderValidation)
```

### "Origin not allowed" CORS Error

**Cause:** Request from unexpected origin

**Fix:** Add origin to allowlist:
```yaml
environment:
  - MCP_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000
```

---

## References

- [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP Authorization Security](https://modelcontextprotocol.io/docs/tutorials/security/authorization)
- [DNS Rebinding Protection Advisory](https://github.com/modelcontextprotocol/typescript-sdk/security/advisories/GHSA-w48q-cv73-mx4w)
- [Red Hat: MCP Security Risks](https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls)
- [Corgea: Securing MCP Servers](https://corgea.com/Learn/securing-model-context-protocol-(mcp)-servers-threats-and-best-practices)

---

## Related Documentation

- [MCP Setup Guide](./MCP_SETUP.md) - Initial setup and configuration
- [MCP Architecture Decision](./MCP_ARCHITECTURE_DECISION.md) - Why we chose this approach
- [Admin MCP Guide](../admin-manual/mcp-admin-guide.md) - End-user guide for administrators

---

*Document created from Session 012 debugging of multi-agent MCP access issues.*
