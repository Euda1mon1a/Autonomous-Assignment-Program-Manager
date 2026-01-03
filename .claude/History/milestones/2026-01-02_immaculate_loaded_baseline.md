# Milestone: Immaculate Loaded Baseline

**Date:** 2026-01-02 (Hawaii) / 2026-01-03 (UTC)
**Session:** 052B
**PR:** #612
**Branch:** `fix/system-hardening-2026-01-02-b`

---

## Summary

Established the **Immaculate Loaded** baseline - a verified, fully-functional system state with:
- All services healthy and tested
- MCP tools working (verified via tool call)
- Database schema at head (50+ migrations applied)
- **Jan 1 scheduling data loaded and verified**

This milestone represents the production-ready state for Block 10 schedule generation.

---

## Data Contents

| Table | Count | Description |
|-------|-------|-------------|
| people | 29 | Residents and faculty roster |
| assignments | 994 | Schedule assignments |
| absences | 153 | Leave and absence records |
| blocks | 730 | AM/PM blocks for scheduling |
| rag_documents | 185 | RAG knowledge base documents |

**Data Source:** `backups/data/residency_scheduler_20260101_121727.sql.gz`

---

## Assets Created

### Docker Image Tags

```
backend:immaculate-loaded
mcp-server:immaculate-loaded
frontend:immaculate-loaded
celery-worker:immaculate-loaded
celery-beat:immaculate-loaded
```

### Backup Archive

```
backups/immaculate/immaculate_loaded_20260102_215650.tar.gz
```

Contents:
- `db_dump.sql` - PostgreSQL dump (schema + Jan 1 data)
- `.mcp.json` - MCP configuration
- `docker-compose.yml` - Container orchestration
- `docker-entrypoint.sh` - Backend entrypoint (migrations enabled)
- `scheduler_mcp_src/` - MCP server source
- `git_commit.txt` - Git state reference
- `MANIFEST.md` - Restoration instructions

---

## Backup Hierarchy (Updated)

| Tier | Tag | Archive | Description |
|------|-----|---------|-------------|
| IMMACULATE | `*:immaculate-empty` | `immaculate_empty_20260102_213208.tar.gz` | Schema only, zero data |
| IMMACULATE | `*:immaculate-loaded` | `immaculate_loaded_20260102_215650.tar.gz` | Schema + Jan 1 data |
| SACRED | `*:sacred-612` | `sacred_612_20260102_212112.tar.gz` | PR 612 milestone |

---

## Restoration Commands

```bash
# Restore Docker images
docker tag backend:immaculate-loaded autonomous-assignment-program-manager-backend:latest
docker tag mcp-server:immaculate-loaded autonomous-assignment-program-manager-mcp-server:latest
docker tag frontend:immaculate-loaded autonomous-assignment-program-manager-frontend:latest
docker tag celery-worker:immaculate-loaded autonomous-assignment-program-manager-celery-worker:latest
docker tag celery-beat:immaculate-loaded autonomous-assignment-program-manager-celery-beat:latest

# Restart stack
docker compose down
docker compose up -d

# Restore database (if wiped)
tar -xzf backups/immaculate/immaculate_loaded_20260102_215650.tar.gz -C backups/immaculate/
cat backups/immaculate/immaculate_loaded_20260102_215650/db_dump.sql | \
  docker compose exec -T db psql -U scheduler -d residency_scheduler
```

---

## Difference from Immaculate Empty

| Aspect | Immaculate Empty | Immaculate Loaded |
|--------|------------------|-------------------|
| Schema | Full (50+ migrations) | Full (50+ migrations) |
| Admin user | Yes | Yes |
| Roster data | No | 29 people |
| Assignments | No | 994 assignments |
| Absences | No | 153 absences |
| Blocks | No | 730 blocks |
| RAG documents | No | 185 documents |
| Use case | Fresh start | Production ready |

---

## Related Documents

- `.claude/History/milestones/2026-01-02_immaculate_empty_baseline.md` - Empty baseline
- `.claude/History/incidents/2026-01-02_infrastructure_mcp_rebuild.md` - Death spiral incident
- `.claude/Scratchpad/SESSION_052B_HANDOFF.md` - Session handoff

---

*This milestone establishes the production-ready baseline for Block 10 schedule generation.*
