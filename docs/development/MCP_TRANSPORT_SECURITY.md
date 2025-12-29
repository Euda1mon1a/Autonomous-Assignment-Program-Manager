# MCP Transport Configuration & Security Guide

> **Updated:** 2025-12-29
> **Purpose:** Configure MCP transport for security and multi-agent concurrency

---

## Table of Contents

1. [Transport Types Overview](#transport-types-overview)
2. [STDIO vs HTTP: When to Use Each](#stdio-vs-http-when-to-use-each)
3. [Multi-Agent Concurrency Issue](#multi-agent-concurrency-issue)
4. [Secure HTTP Configuration](#secure-http-configuration)
5. [Configuration Examples](#configuration-examples)
6. [Security Checklist](#security-checklist)
7. [Troubleshooting](#troubleshooting)

---

## Transport Types Overview

MCP (Model Context Protocol) supports multiple transport mechanisms:

| Transport | Use Case | Concurrency | Security |
|-----------|----------|-------------|----------|
| **STDIO** | Local development, single agent | Single client | Inherently safe (no network) |
| **HTTP** | Multi-agent, remote access | Many clients | Requires configuration |
| **SSE** | Legacy remote (deprecated) | Many clients | Being phased out |

### Key Architectural Difference

```
STDIO Transport:
Claude Code Session ──(single pipe)──> MCP Server Process

HTTP Transport:
Claude Code Session A ──┐
Claude Code Session B ──┼──(HTTP)──> MCP Server (port 8080)
Spawned Agent C ────────┘
```

**Source:** [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)

---

## STDIO vs HTTP: When to Use Each

### Use STDIO When

- Single Claude Code session (no parallel agents using MCP)
- Maximum simplicity desired
- No network exposure needed
- Local development only

### Use HTTP When

- Spawning agents that need MCP tool access
- Running parallel MCP tool calls
- IDE integration (VSCode, Cursor, Zed)
- Multiple developers sharing one MCP server

---

## Multi-Agent Concurrency Issue

### The Problem

When using STDIO transport with Claude Code's Task tool (subagents):

1. Main session holds the STDIO pipe
2. Spawned agents cannot acquire the pipe
3. Agents see "Not connected" or "Permission prompts unavailable"
4. MCP tools appear blocked even though server is healthy

### Evidence

From Session 012 testing with 5 parallel agents:

| Agent | MCP Result | Cause |
|-------|------------|-------|
| Stream A | 0/4 tools | Pipe contention |
| Stream B | 4/13 tools | First to acquire pipe |
| Stream C | Timeout | Pipe busy |
| Stream D | 0/10 tools | Pipe contention |

### Root Cause

From [MCP specification](https://modelcontextprotocol.io/docs/learn/architecture):

> "Local MCP servers that use the STDIO transport typically serve a **single MCP client**, whereas remote MCP servers that use the Streamable HTTP transport will typically serve **many MCP clients**."

### The Fix

Switch to HTTP transport for multi-agent workloads. See [Secure HTTP Configuration](#secure-http-configuration).

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
      "transport": "http"
    }
  }
}
```

#### 3. Keep STDIO as Fallback (Optional)

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://127.0.0.1:8080/mcp",
      "transport": "http"
    },
    "residency-scheduler-stdio": {
      "command": "docker",
      "args": ["compose", "exec", "-T", "mcp-server", "python", "-m", "scheduler_mcp.server"],
      "transport": "stdio",
      "disabled": true
    }
  }
}
```

---

## Configuration Examples

### Development (Single Developer, No Agents)

Use STDIO for simplicity:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "docker",
      "args": ["compose", "exec", "-T", "mcp-server", "python", "-m", "scheduler_mcp.server"],
      "transport": "stdio"
    }
  }
}
```

### Development (Multi-Agent Workflows)

Use HTTP for concurrency:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "url": "http://127.0.0.1:8080/mcp",
      "transport": "http"
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
      "transport": "http",
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
      "transport": "http",
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
