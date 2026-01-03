# Session 052: Infrastructure Rebuild Complete

> **CORRECTION (Session 052b):** MCP config field is `"type": "http"` NOT `"transport": "http"`.
> The validation script and Claude Code schema require `type` field. Updated in PR #612.

> **Date:** 2026-01-02 (Hawaii) / 2026-01-03 (UTC)
> **Branch:** `fix/system-hardening-2026-01-02-b`
> **PR:** #611
> **Trigger:** Recurring MCP connection failures across 6+ sessions

---

## ✅ Infrastructure Rebuild Complete

**All 6 Phases Completed:**

| Phase | Status | Result |
|-------|--------|--------|
| 1. Teardown | ✅ | Reclaimed 1.038GB (113 volumes → 2) |
| 2. Verify Configs | ✅ | All match PR 608 |
| 3. Fix VSCode MCP | ✅ | SSE → HTTP |
| 4. Rebuild Containers | ✅ | All 5 services rebuilt |
| 5. Verify Health | ✅ | All endpoints responding |
| 6. Sacred Backup | ✅ | `backup_20260102_203326.tar.gz` (928MB) |

---

## Sacred Container Tags Created

```
backend:sacred-608       3.35GB
mcp-server:sacred-608    756MB
frontend:sacred-608      431MB
```

**To restore containers to this state later:**
```bash
docker tag backend:sacred-608 autonomous-assignment-program-manager-backend:latest
docker tag mcp-server:sacred-608 autonomous-assignment-program-manager-mcp-server:latest
docker tag frontend:sacred-608 autonomous-assignment-program-manager-frontend:latest
docker compose up -d
```

---

## Root Cause Analysis

### The Problem
MCP server connections failing intermittently across multiple sessions.

### Root Causes Identified
1. **Config Drift:** Three MCP configs with conflicting values
   - `.mcp.json` (project) - had correct `transport: http`
   - `.vscode/mcp.json` - had WRONG `type: sse`
   - `~/.claude/config.json` - field name inconsistencies

2. **Docker Volume Bloat:** 113 orphaned volumes accumulated

3. **Snapshot Timing:** Jan 2 snapshot was created BEFORE PR 608 merge

### The Fix
- Full teardown (`docker compose down -v --rmi local`)
- Restored ALL configs to PR 608 commit `e6c4440e` state
- FastMCP pinned to `==2.14.2` (known working version)
- Field standardized to `transport: http` (not `type: sse`)

---

## Critical Files (PR 608 State)

### `.mcp.json`
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

### `.vscode/mcp.json`
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

### `mcp-server/pyproject.toml`
```toml
dependencies = [
    "fastmcp==2.14.2",  # PINNED: Exact version known to work
    ...
]
```

---

## Next Steps (For Discussion)

### Database Options
1. **Restore from Jan 1 backup** - Has 730 blocks, 29 people, full data
2. **Fresh seed** - Run database seeding scripts
3. **Keep current state** - Empty DB if acceptable

### Migrations
- `backend/docker-entrypoint.sh` currently has migrations disabled
- Re-enable after alembic version is reconciled with chosen database state

---

## Lessons Learned

1. **Pin versions explicitly** - FastMCP `==2.14.2` not `>=`
2. **Config field names matter** - `transport` not `type`
3. **Snapshot timing relative to PRs** - Document when snapshots were taken
4. **Container version control** - Tag images as `sacred-NNN` after successful builds
5. **Three config locations** - Must keep `.mcp.json`, `.vscode/mcp.json`, and `~/.claude/config.json` in sync

---

## Backup Artifacts

| Artifact | Location | Size |
|----------|----------|------|
| Full Stack Backup | `backups/backup_20260102_203326.tar.gz` | 928MB |
| Jan 1 Database | `backups/backup_20260101_010830/` | - |
| Sacred Images | Docker local tags `*:sacred-608` | ~4.5GB |

---

*Session 052 - ORCHESTRATOR Mode*
