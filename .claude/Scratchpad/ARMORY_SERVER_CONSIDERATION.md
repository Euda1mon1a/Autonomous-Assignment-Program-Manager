# Armory Server Separation Consideration

> **Status:** Not Yet Needed
> **Created:** 2026-01-11
> **Review When:** Starting to pull tools from armory to core, or experiencing stability issues

---

## Current Architecture

### Core MCP Server (`mcp-server/src/scheduler_mcp/`)

- **Main server.py:** ~5,000 lines, 170KB
- **34 core tools** always loaded (schedule, compliance, swap, resilience, analytics)
- **14 specialized tool modules** (thermodynamics, Hopfield, VAR, Kalman, game theory, etc.)
- Full middleware stack (auth, rate limiting, logging, error handling)

### Armory (`mcp-server/src/scheduler_mcp/armory/`)

**~50 exotic tools across 5 scientific domains:**

| Domain | Tools | Examples |
|--------|-------|----------|
| physics/ | 12 | Thermodynamics, Hopfield networks, time crystals |
| biology/ | 14 | Epidemiology, immune systems, gene regulation |
| operations_research/ | 10 | Queuing theory, game theory, Six Sigma |
| resilience_advanced/ | 8 | Homeostasis, cognitive load, stigmergy |
| fatigue_detailed/ | 6 | Low-level FRMS components |

**Loading:** Lazy via `ARMORY_DOMAINS` env var - elegant on-demand activation

---

## Assessment: Should Armory Be Its Own Server?

| Consideration | Current | Verdict |
|--------------|---------|---------|
| **Complexity** | server.py = 5K lines | ⚠️ Significant, but armory cleanly isolated |
| **Cognitive Load** | Hidden by default | ✅ Good design |
| **Deployment Flexibility** | Set ARMORY_DOMAINS=none | 🔸 Marginal gain from split |
| **Scaling** | Shared process | 🔸 Only matters if armory CPU-heavy |
| **Blast Radius** | Armory bug → MCP down | ⚠️ Risk exists |
| **Latency** | Zero network hop | ✅ Fast internal calls |
| **Auth/Secrets** | Shared | ✅ Would need duplication if split |
| **Maintenance** | Single deployment | ⚠️ Two servers = 2x operational overhead |

---

## Recommendation: Not Yet

The current design is elegant—lazy loading via environment variable achieves the main goal (keeping everyday toolkit lean) without the operational overhead of a second server.

---

## Consider Splitting If:

1. **CPU/Memory:** Armory tools start consuming significant resources (e.g., running actual optimization solvers)

2. **Independent Scaling:** You need to scale research-grade tools separately from core operations

3. **Stability Issues:** Armory bugs start cascading to core functionality

4. **Access Control:** You want to gate armory access with different authentication (e.g., research team only)

5. **Container Size:** Build times or image size become problematic

---

## Alternative to Splitting

Build a slimmed "production" Docker image that excludes armory entirely:

```dockerfile
# Dockerfile.slim
COPY --exclude armory mcp-server/src/scheduler_mcp /app/
```

---

## Key Insight

The lazy-load pattern already in place is the right abstraction layer. If physical isolation becomes necessary later, the domain separation work is already done.

---

## Related Files

- `mcp-server/src/scheduler_mcp/armory/README.md` - Armory documentation
- `mcp-server/src/scheduler_mcp/armory/loader.py` - Lazy loading implementation
- `mcp-server/src/scheduler_mcp/server.py` - Main MCP server

---

*Review this document when promoting armory tools to core or experiencing MCP stability issues.*
