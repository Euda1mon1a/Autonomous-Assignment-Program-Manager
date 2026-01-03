# Session 052: MCP Infrastructure Rebuild

> **Date:** 2026-01-02/03
> **Branch:** `fix/system-hardening-2026-01-02-b`
> **PR:** #611
> **Status:** IN PROGRESS - MCP still not connecting

---

## Executive Summary

Full infrastructure burn and restore from backup. Stack is up but Claude Code still says "No MCP servers configured" despite correct project-level `.mcp.json`.

---

## Root Cause Analysis: MCP Config Chaos

### The Problem: THREE Conflicting MCP Configs

| Location | Field Name | Value | URL | Status |
|----------|------------|-------|-----|--------|
| `.mcp.json` (project) | `type` | `http` | `http://127.0.0.1:8080/mcp` | **CORRECT** |
| `.vscode/mcp.json` | `type` | `sse` | `http://127.0.0.1:8080/mcp/sse` | **WRONG** |
| `~/.claude/config.json` | `transport` | `http` | `http://127.0.0.1:8080/mcp` | **WRONG FIELD** |

### Claude Code Config Precedence (Hypothesis)

Claude Code may read MCP config from:
1. `~/.claude/config.json` (user-level) - TAKES PRECEDENCE?
2. `.mcp.json` (project-level)
3. `.vscode/mcp.json` (VSCode integration)

If `~/.claude/config.json` uses `transport` instead of `type`, schema validation may reject it entirely.

### The Correct Schema

Per Sessions 047-050 documentation:
```json
{
  "mcpServers": {
    "server-name": {
      "type": "http",           // NOT "transport"
      "url": "http://host:port/mcp"
    }
  }
}
```

- **Field must be `type`** not `transport`
- **Value must be `http`** for HTTP transport (not `sse`)
- **URL path must be `/mcp`** (not `/mcp/sse`)

---

## Infrastructure Status After Rebuild

### Docker Containers

| Container | Status | Port |
|-----------|--------|------|
| backend | healthy | 8000 |
| frontend | unhealthy | 3000 |
| db | healthy | 5432 |
| redis | healthy | 6379 |
| mcp-server | healthy | 8080 |
| celery-worker | healthy | - |
| celery-beat | healthy | - |
| n8n | healthy | 5678 |

### Health Endpoints

```bash
curl http://localhost:8000/health
# {"status":"healthy","database":"connected"}

curl http://localhost:8080/health
# {"status":"healthy","service":"residency-scheduler-mcp","version":"0.1.0",...}
```

### Database State

| Table | Count | Expected |
|-------|-------|----------|
| blocks | 730 | 730 ✓ |
| people | 29 | 28+ ✓ |
| rotation_templates | 60 | 24+ ✓ |
| assignments | 994 | varies |

Database restored from `backups/postgres/residency_scheduler_20260101_121727.sql.gz`

---

## Actions Taken This Session

### Phase 1: Infrastructure Burn
- Stopped all containers
- Pruned 100+ orphan volumes (reclaimed 13.72 GB)
- Cleaned up images

### Phase 2: Restore from Snapshot
- Extracted `backups/mcp-fix-snapshot-20260102.tar.gz`
- Found snapshot had minimal data (4 blocks, 0 people)
- Switched to Jan 1 backup which had full data

### Phase 3: Database Restore
- Restored from `residency_scheduler_20260101_121727.sql.gz`
- Fixed alembic version mismatch (stamped to `20260101_import_staging`)
- Disabled auto-migrations in `docker-entrypoint.sh` (temporary)

### Phase 4: MCP Config Restore
- COORD_PLATFORM restored `.mcp.json` from snapshot with correct config
- Discovered conflicting configs in `.vscode/mcp.json` and `~/.claude/config.json`

---

## Code Changes Made

### 1. docker-entrypoint.sh (TEMPORARY)
```bash
# Disabled auto-migrations to bypass alembic version conflict
echo "Skipping migrations (manual control)..."
# alembic upgrade head
```
**TODO:** Re-enable once migration state is fixed

### 2. channels.py rename (from COORD_PLATFORM agent)
```
backend/app/notifications/channels.py → channels_core.py
backend/app/notifications/channels/__init__.py (created)
```
**Reason:** Python import conflict between `channels.py` and `channels/` directory

### 3. PATCH endpoint added (from COORD_FRONTEND agent)
```python
# backend/app/api/routes/admin_users.py
@router.patch("/{user_id}")  # Added alongside @router.put
```

### 4. Lint fixes (from COORD_FRONTEND agent)
- Fixed unused error variables in `auth.ts`, `lazy-loader.ts`
- Added `caughtErrorsIgnorePattern` to `.eslintrc.json`

---

## Pending Issues

### 1. MCP Not Connecting to Claude Code
**Status:** BLOCKING
**Symptom:** `/mcp` returns "No MCP servers configured"
**Root Cause:** Config precedence or schema validation failure

**Fix Required:**
```bash
# Option A: Fix user-level config
cat > ~/.claude/config.json << 'EOF'
{
  "mcpServers": {
    "residency-scheduler": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
EOF

# Option B: Remove conflicting configs
rm ~/.claude/config.json
rm .vscode/mcp.json
# Keep only .mcp.json
```

### 2. Frontend Unhealthy
**Status:** Not investigated
**Symptom:** Container shows "unhealthy"

### 3. Alembic Migration State
**Status:** Workaround in place
**Issue:** Backup has newer schema than alembic_version indicates
**Fix:** Need to properly stamp or reconcile migration history

### 4. Backup Strategy
**Status:** Needs improvement
**Issue:** Jan 2 snapshot had minimal data, inconsistent alembic state
**Fix:** Improve backup validation and include alembic version verification

---

## All Config Files

### .mcp.json (PROJECT - CORRECT)
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

### .vscode/mcp.json (WRONG - uses SSE)
```json
{
  "mcpServers": {
    "residency-scheduler": {
      "type": "sse",
      "url": "http://127.0.0.1:8080/mcp/sse"
    }
  }
}
```

### ~/.claude/config.json (WRONG FIELD NAME)
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

### .claude/settings.json (Permissions)
```json
{
  "permissions": {
    "allow": ["mcp__*", ...],
    ...
  }
}
```

### .antigravity/settings.json
```json
{
  "autopilot": { "enabled": true, "mode": "A" },
  ...
}
```

---

## Next Steps

1. **Fix MCP Config Priority:**
   - Update `~/.claude/config.json` to use `type` instead of `transport`
   - OR remove it and rely on project `.mcp.json`
   - Sync `.vscode/mcp.json` to match project config

2. **Restart Claude Code** to reload MCP config

3. **Verify MCP Connection:**
   ```bash
   /mcp  # Should list residency-scheduler tools
   ```

4. **Fix Frontend Health Check**

5. **Create Fresh Backup** once system is stable

6. **Update restore_full_stack.sh** to handle `.dump` format

---

## Session Artifacts

- **Snapshot used:** `backups/mcp-fix-snapshot-20260102.tar.gz` (minimal data)
- **DB backup used:** `backups/postgres/residency_scheduler_20260101_121727.sql.gz`
- **Agents spawned:** COORD_PLATFORM, COORD_FRONTEND
- **Disk reclaimed:** 13.72 GB from orphan volumes

---

*Session ongoing - MCP connection not yet verified*
