---
name: mcp-recovery
description: Diagnose and recover MCP server when tools fail. Covers health checks, watchdog verification, port conflicts, backend dependency, and manual restart.
model_tier: haiku
parallel_hints:
  can_parallel_with: [stack-audit, systematic-debugger]
  must_serialize_with: []
  preferred_batch_size: 1
context_hints:
  max_file_context: 10
  compression_level: 2
  requires_git_context: false
  requires_db_context: false
escalation_triggers:
  - pattern: "restart.*fail.*3"
    reason: "MCP failed to start after multiple attempts — check Python environment"
  - pattern: "port.*8080.*occupied"
    reason: "Unknown process on MCP port requires investigation"
---

# MCP Recovery

> **Purpose:** Diagnose and recover the MCP server (97+ AI tools) when it goes down
> **Created:** 2026-02-20
> **Trigger:** `/mcp-recovery`
> **Aliases:** `/mcp-fix`, `/fix-mcp`

---

## When This Skill Activates

- `mcp__residency-scheduler__*` tool calls return errors or timeouts
- Claude Code shows "MCP server not available" or connection refused
- Session startup with no MCP tools listed
- After system sleep/wake, reboot, or terminal session end
- RAG queries returning 500 errors

---

## Quick Triage (30 seconds)

Run all three checks in parallel:

```bash
# 1. MCP server health
curl -sf --max-time 5 http://127.0.0.1:8080/health && echo "MCP: UP" || echo "MCP: DOWN"

# 2. Backend dependency (MCP tools need this)
curl -sf --max-time 5 http://127.0.0.1:8000/health && echo "Backend: UP" || echo "Backend: DOWN"

# 3. Watchdog agent status
launchctl list | grep aapm && echo "Watchdog: LOADED" || echo "Watchdog: NOT LOADED"
```

### Decision Tree

```
MCP UP + Backend UP     → Tools should work. Check RAG warming (wait 30s).
MCP UP + Backend DOWN   → MCP is alive but tools will fail. Start backend.
MCP DOWN + Watchdog ON  → Watchdog will restart within 60s. Check mcp.log for crash.
MCP DOWN + Watchdog OFF → Load watchdog or manual restart.
```

---

## Common Failure Modes

| # | Mode | Symptom | Root Cause | Fix |
|---|------|---------|------------|-----|
| 1 | MCP down, watchdog cycling | Watchdog log shows repeated restarts | MCP crashes on startup (Python error) | Check `logs/native/mcp.log` for traceback |
| 2 | MCP down, no watchdog | Tools fail, nothing in `launchctl list` | Watchdog never loaded or was unloaded | Load the launchd plist (see Recovery #2) |
| 3 | MCP up, tools fail | Health returns 200 but tool calls error | Backend on :8000 is down | Start backend via `scripts/start-native.sh` |
| 4 | Port conflict | MCP can't bind to 8080 | Docker container or stale process holding port | `lsof -ti :8080` then kill the process |
| 5 | RAG warming | 500 errors for ~30s after fresh start | Embedding model + document index loading | Wait 30 seconds, then retry |
| 6 | Stale PID | Watchdog kills wrong process or skips restart | PID file points to dead/recycled PID | Delete `/tmp/residency-scheduler/mcp.pid` |
| 7 | Client config wrong location | Server healthy but `/mcp` reconnect always fails | Config in `~/.claude/config.json` instead of `~/.claude.json` project section | Run `claude mcp add --transport http --scope local` (see Recovery #7) |

---

## Recovery Procedures

### Recovery #1: Wait for Watchdog (Easiest)

If the watchdog is loaded (`launchctl list | grep aapm` shows it), just wait up to 60 seconds. The watchdog runs every 60s and will auto-restart MCP.

```bash
# Watch for restart in real-time
tail -f logs/native/mcp-watchdog.log
```

### Recovery #2: Load Watchdog

If the watchdog is not loaded:

```bash
launchctl load ~/Library/LaunchAgents/com.aapm.mcp-watchdog.plist
```

This starts the watchdog immediately (`RunAtLoad`) and it will restart MCP on its first run.

### Recovery #3: Manual Restart (Immediate)

Run the watchdog script directly — no need to wait for launchd:

```bash
./scripts/watchdog-mcp.sh
```

This performs the full health check → kill stale → restart cycle immediately.

### Recovery #4: Start Full Stack

If backend is also down:

```bash
./scripts/start-native.sh
```

This starts PostgreSQL, backend, frontend, Celery, and MCP in order.

### Recovery #7: Fix Client Config Location

If the server is healthy (`curl -sf http://127.0.0.1:8080/health`) but Claude Code refuses to connect via `/mcp`:

```bash
# Remove any stale entries
claude mcp remove residency-scheduler 2>/dev/null

# Re-add via CLI (writes to the correct location in ~/.claude.json)
claude mcp add --transport http --scope local residency-scheduler http://127.0.0.1:8080/mcp

# Reconnect
# Then type /mcp in Claude Code
```

**Why this works:** Claude Code reads MCP config from `~/.claude.json` (per-project local scope) with highest priority. Manual edits to `~/.claude/config.json` or `.mcp.json` are lower priority and may not be picked up reliably. The `claude mcp add` CLI writes to the correct location.

**Important:** `--transport http` means Streamable HTTP (not SSE). Do NOT use `--transport sse` — the server only exposes Streamable HTTP endpoints. Do NOT use `--transport stdio` — stdio limits parallel tool calls to one at a time.

### Recovery #5: Nuclear Option

When everything else fails — kill all, clear state, start fresh:

```bash
# Kill anything on MCP port
lsof -ti :8080 | xargs kill -9 2>/dev/null

# Clear stale PID
rm -f /tmp/residency-scheduler/mcp.pid

# Activate virtualenv and start manually
source mcp-server/.venv/bin/activate
cd mcp-server/src
python -m scheduler_mcp.server --host 127.0.0.1 --port 8080 --transport http
```

Note: Manual start runs in foreground (Ctrl+C to stop). For background, use the watchdog instead.

### Recovery #6: Fix Port Conflict

```bash
# Find what's on port 8080
lsof -i :8080

# If Docker container:
docker stop $(docker ps -q --filter "publish=8080")

# If stale process:
kill $(lsof -ti :8080)

# Then let watchdog restart MCP (or run Recovery #3)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/watchdog-mcp.sh` | Health check + double-fork auto-restart |
| `scripts/_native-lib.sh` | Shared env setup (`setup_db_env`, port mappings) |
| `scripts/start-mcp.sh` | Standalone MCP start script |
| `scripts/start-native.sh` | Full native stack launcher |
| `mcp-server/src/scheduler_mcp/server.py` | MCP server entry point (FastMCP 2.x) |
| `~/.claude.json` (projects section) | Claude Code MCP client config (written by `claude mcp add`) |
| `~/.claude/config.json` | Global MCP config (fallback — prefer `claude mcp add`) |
| `~/Library/LaunchAgents/com.aapm.mcp-watchdog.plist` | launchd agent (60s interval + RunAtLoad) |
| `/tmp/residency-scheduler/mcp.pid` | MCP process ID file |
| `logs/native/mcp.log` | MCP server stdout/stderr |
| `logs/native/mcp-watchdog.log` | Watchdog restart events |

---

## Post-Recovery Verification

After any recovery, confirm all four checks pass:

```bash
# 1. Health endpoint
curl -sf http://127.0.0.1:8080/health | python3 -m json.tool

# 2. Watchdog loaded
launchctl list | grep aapm

# 3. PID file valid
PID=$(cat /tmp/residency-scheduler/mcp.pid 2>/dev/null) && kill -0 "$PID" 2>/dev/null && echo "PID $PID alive" || echo "PID invalid"

# 4. Clean logs (no tracebacks)
tail -5 logs/native/mcp.log
tail -5 logs/native/mcp-watchdog.log
```

---

## Architecture Notes

- **Transport:** Streamable HTTP (Starlette/uvicorn via FastMCP 2.x `mcp.http_app(stateless_http=True)`), not stdio. Claude Code connects via `http://127.0.0.1:8080/mcp`. Stdio is NOT used because it limits parallel tool calls to one at a time.
- **Daemon pattern:** Watchdog uses double-fork (`os.fork()` → `os.setsid()` → `os.fork()`) so MCP survives after the watchdog script exits. This is necessary because launchd kills all processes in the watchdog's process group.
- **Backend dependency:** MCP server boots without the backend, but all 97+ tools that proxy to the FastAPI backend will fail. The health endpoint still returns 200 (MCP itself is fine).
- **RAG warming:** After a cold start, RAG queries may 500 for ~30 seconds while the embedding model and document index load. This is normal.
- **Port 8080:** Native MCP always uses 8080. Docker MCP uses 8081 (for future containerized use). They never run simultaneously.

### Claude Code Client Config (Critical)

Claude Code discovers MCP servers from multiple config locations with this precedence:

| Priority | Location | Scope | Written by |
|----------|----------|-------|------------|
| 1 | `~/.claude.json` → `projects["/path/to/repo"].mcpServers` | Per-project local | `claude mcp add --scope local` |
| 2 | `.mcp.json` (repo root) | Project (shared) | Manual edit |
| 3 | `~/.claude/config.json` → `mcpServers` | Global | Manual edit |

**The canonical way to register the MCP server:**

```bash
claude mcp add --transport http --scope local residency-scheduler http://127.0.0.1:8080/mcp
```

This writes to `~/.claude.json` under the project key, which is the most reliable path. Manual edits to `~/.claude/config.json` or `.mcp.json` may not be picked up after `/mcp` reconnect.

**If `/mcp` reconnect fails after config changes**, fully quit and relaunch Claude Code from a new terminal — the MCP client caches connection state within a session.

---

## Related Skills

| Skill | When to Use Instead |
|-------|-------------------|
| `/stack-audit` | Full infrastructure health check (10 checks including MCP) |
| `/systematic-debugger` | Complex bugs requiring root cause analysis |
| `/health-check` | Quick overall system health snapshot |

---

*Watchdog script: `scripts/watchdog-mcp.sh` | launchd plist: `~/Library/LaunchAgents/com.aapm.mcp-watchdog.plist`*
