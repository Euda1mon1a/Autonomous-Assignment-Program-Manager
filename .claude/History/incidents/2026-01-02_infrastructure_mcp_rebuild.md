# Infrastructure Incident: MCP Connection Failures & Full Rebuild

**Summary:** Full infrastructure teardown and rebuild to resolve recurring MCP connection failures spanning 6+ sessions.

**Date:** 2026-01-02 (Hawaii) / 2026-01-03 (UTC)
**Session:** 052
**Branch:** `fix/system-hardening-2026-01-02-b`
**PR:** #611
**Severity:** HIGH (blocking AI agent operations)

---

## Context

MCP (Model Context Protocol) server connections failing intermittently across multiple sessions. Symptoms:
- `/mcp` returning "No MCP servers configured"
- Inconsistent tool availability
- Session-to-session config drift

## Root Cause Analysis

### Primary Causes

1. **Config Drift Across Three Locations**
   - `.mcp.json` (project) - had correct `transport: http`
   - `.vscode/mcp.json` - had WRONG `type: sse`
   - `~/.claude/config.json` - field name inconsistencies

2. **Docker Volume Bloat**
   - 113 orphaned volumes accumulated
   - Stale container state causing inconsistent behavior

3. **Snapshot Timing Issue**
   - Jan 2 snapshot was created at 14:31 HST
   - PR 608 (the known-good state) merged at 16:49 HST
   - Snapshot predated the fix

### Contributing Factors

- FastMCP version not pinned (allowing drift)
- Field name inconsistency (`transport` vs `type`)
- No automated config validation between locations

---

## Resolution

### 6-Phase Recovery Plan

| Phase | Action | Result |
|-------|--------|--------|
| 1. Teardown | `docker compose down -v --rmi local` | Reclaimed 1.038GB (113 → 2 volumes) |
| 2. Verify Configs | Extracted from PR 608 commit `e6c4440e` | All match PR 608 |
| 3. Fix VSCode MCP | Changed `type: sse` → `transport: http` | Config synced |
| 4. Rebuild Containers | `docker compose build --no-cache` | 5 services rebuilt |
| 5. Verify Health | Tested all endpoints | All responding |
| 6. Sacred Backup | Created `backup_20260102_203326.tar.gz` | 928MB |

### Critical Config State (PR 608)

**`.mcp.json` and `.vscode/mcp.json`:**
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

**`mcp-server/pyproject.toml`:**
```toml
"fastmcp==2.14.2",  # PINNED: Exact version known to work
```

---

## Outcome

✅ All services healthy:
- Backend: `http://localhost:8000/health` → `{"status":"healthy"}`
- MCP: `http://localhost:8080/health` → `{"status":"healthy"}`
- Frontend: `http://localhost:3000` → 200 OK
- Database, Redis, Celery: All healthy

✅ Sacred container tags created:
- `backend:sacred-608` (3.35GB)
- `mcp-server:sacred-608` (756MB)
- `frontend:sacred-608` (431MB)

---

## Impact

- **Affected:** AI agent operations across 6+ sessions
- **Duration:** Multiple days of intermittent failures
- **Recovery Time:** ~15 minutes for full rebuild

---

## Preventive Measures

### Implemented

1. **Version Pinning:** FastMCP `==2.14.2` (exact version)
2. **Config Standardization:** All configs use `transport: http` field
3. **Sacred Image Tags:** Known-good images tagged as `*:sacred-608`
4. **Full Stack Backup:** `backup_20260102_203326.tar.gz` (928MB)

### Recommended

1. **Automated Config Validation:** Pre-commit hook to verify config consistency
2. **Container Registry:** Push sacred images to registry for team access
3. **Snapshot Documentation:** Always record snapshot timing relative to PRs
4. **Volume Cleanup Schedule:** Weekly orphan volume pruning

---

## Container Restoration Commands

To restore to this known-good state:
```bash
docker tag backend:sacred-608 autonomous-assignment-program-manager-backend:latest
docker tag mcp-server:sacred-608 autonomous-assignment-program-manager-mcp-server:latest
docker tag frontend:sacred-608 autonomous-assignment-program-manager-frontend:latest
docker compose up -d
```

---

## Related Artifacts

| Artifact | Location |
|----------|----------|
| Full Stack Backup | `backups/backup_20260102_203326.tar.gz` |
| Session Scratchpad | `.claude/Scratchpad/SESSION_052_INFRASTRUCTURE_REBUILD.md` |
| Known-Good Commit | `e6c4440e` (PR 608) |
| Sacred Image Tags | `*:sacred-608` (Docker local) |

---

## Follow-Up Actions

- [ ] Re-enable migrations in `backend/docker-entrypoint.sh` after alembic reconciliation
- [ ] Database restore decision (Jan 1 backup vs fresh seed)
- [ ] Consider GitHub Container Registry for sacred images
- [ ] Add pre-commit hook for MCP config validation

---

**Recorded By:** ORCHESTRATOR (Session 052)
**Reviewed By:** Pending
