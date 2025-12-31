# Session Startup TODOs for Claude Code

> **Purpose:** Explicit step-by-step instructions for Claude Code when starting a new session
> **IMPORTANT:** Complete these TODOs in order before doing any work

---

## Phase 1: Environment Verification

### TODO 1.1: Check Current Branch
```bash
git branch --show-current
git status
```
- [ ] Confirm on correct branch (should be `claude/*` for AI work)
- [ ] If on `main`, create feature branch: `git checkout -b claude/<task>-<id> origin/main`

### TODO 1.2: Check Docker Status
```bash
docker compose ps 2>/dev/null || echo "Docker not available"
```

**If Docker is NOT running or shows containers down:**
- [ ] Start Docker services: `docker compose up -d`
- [ ] Wait 30 seconds for services to initialize
- [ ] Re-check: `docker compose ps`

**Expected running services:**
| Service | Status |
|---------|--------|
| `db` | Up (healthy) |
| `redis` | Up (healthy) |
| `backend` | Up (healthy) |
| `mcp-server` | Up (healthy) |
| `frontend` | Up (optional) |

### TODO 1.3: Verify MCP Server Connectivity
```bash
docker compose exec -T mcp-server python -c "from scheduler_mcp.server import mcp; print(f'MCP Ready: {len(mcp._tools)} tools')"
```

**Expected output:** `MCP Ready: 36 tools` (or similar count)

**If FAILS:**
- [ ] Check MCP logs: `docker compose logs mcp-server --tail 50`
- [ ] Restart MCP: `docker compose restart mcp-server`
- [ ] Wait 10 seconds, retry

### TODO 1.4: Verify Backend API
```bash
docker compose exec -T mcp-server curl -s http://backend:8000/health | head -c 200
```

**Expected:** JSON response with health status

**If FAILS:**
- [ ] Check backend logs: `docker compose logs backend --tail 50`
- [ ] Check database: `docker compose logs db --tail 20`
- [ ] Restart if needed: `docker compose restart backend`

---

## Phase 2: Context Loading

### TODO 2.1: Load Project Guidelines
- [ ] Read `CLAUDE.md` (root of project)
- [ ] Note: Tech stack, architecture, testing requirements

### TODO 2.2: Load AI Rules
- [ ] Read `.claude/CONSTITUTION.md`
- [ ] Note: Safety rules, forbidden actions, escalation protocols

### TODO 2.3: Load Skill Index
- [ ] Read `.claude/SKILL_INDEX.md`
- [ ] Note: 34 skills available, routing rules, intent mappings

### TODO 2.4: Load MCP Usage Guide
- [ ] Read `.claude/MCP_USAGE_TODOS.md`
- [ ] Note: Tool reference, error handling, logging requirements

---

## Phase 3: State Check

### TODO 3.1: Check Recent Activity
```bash
ls -la .claude/History/scheduling/ 2>/dev/null | tail -5
ls -la .claude/History/swaps/ 2>/dev/null | tail -5
ls -la .claude/History/resilience/ 2>/dev/null | tail -5
```
- [ ] Note any recent operations
- [ ] Check for incomplete operations (files ending in `.partial` or `.tmp`)

### TODO 3.2: Check for Active Incidents
```bash
ls -la docs/incidents/INCIDENT_*.md 2>/dev/null | tail -3
```
- [ ] If active incident exists, prioritize incident response

### TODO 3.3: Check Test Status
```bash
cd backend && python -m pytest --collect-only 2>/dev/null | tail -5
```
- [ ] Note if tests are runnable
- [ ] If errors, may need to fix environment

---

## Phase 4: Ready Confirmation

### TODO 4.1: Summarize Status
Report to user:
```
Session Ready:
- Branch: [current branch]
- Docker: [running/not running]
- MCP Server: [ready with X tools / not ready]
- Backend API: [healthy / issues]
- Recent Activity: [summary or none]
```

### TODO 4.2: Await User Command
- [ ] Ready to receive user requests
- [ ] Route to appropriate skill based on intent (see SKILL_INDEX.md)

---

## Quick Start Commands

### If Everything is Down (Cold Start)
```bash
# 1. Start all services
docker compose up -d

# 2. Wait for health checks (30 seconds)
sleep 30

# 3. Verify
docker compose ps
docker compose exec -T mcp-server python -c "from scheduler_mcp.server import mcp; print('OK')"
docker compose exec -T mcp-server curl -s http://backend:8000/health
```

### If Just MCP Needs Restart
```bash
docker compose restart mcp-server
sleep 10
docker compose exec -T mcp-server python -c "from scheduler_mcp.server import mcp; print('OK')"
```

### If Backend Needs Restart
```bash
docker compose restart backend
sleep 15
docker compose exec -T mcp-server curl -s http://backend:8000/health
```

---

## Troubleshooting Checklist

### MCP Import Error
**Symptom:** `ModuleNotFoundError: No module named 'fastmcp'`
**Cause:** Running Python locally instead of in Docker
**Fix:** Ensure `.mcp.json` uses `docker compose exec` command

### Backend Connection Refused
**Symptom:** `curl: (7) Failed to connect to backend port 8000`
**Cause:** Backend container not running or not healthy
**Fix:**
1. `docker compose ps backend`
2. `docker compose logs backend --tail 50`
3. Check database: `docker compose ps db`

### Database Connection Error
**Symptom:** Backend logs show `connection refused` to postgres
**Cause:** Database not ready
**Fix:**
1. `docker compose ps db`
2. `docker compose logs db --tail 20`
3. Wait or restart: `docker compose restart db`

### Redis Connection Error
**Symptom:** Celery tasks fail, rate limiting errors
**Cause:** Redis not running
**Fix:**
1. `docker compose ps redis`
2. `docker compose restart redis`

---

## Session End TODOs

Before ending a session:

1. [ ] Commit any changes: `git add . && git commit -m "WIP: <description>"`
2. [ ] Push to remote: `git push -u origin <branch>`
3. [ ] Document incomplete work in `.claude/Scratchpad/`
4. [ ] Log session summary if significant work done

---

**END OF SESSION STARTUP TODOS**

*Complete Phase 1-3 before accepting user commands. Phase 4 confirms readiness.*
