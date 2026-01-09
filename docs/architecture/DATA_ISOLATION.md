# Data Isolation & Disaster Recovery

> **Purpose:** Document what data is local-only vs synced to git, and how to recover after hardware failure.
> **Last Updated:** 2026-01-09

---

## Executive Summary

This project separates data into two categories:

1. **Synced (Sacred Timeline):** Code, schemas, configs, docs - recoverable from `git clone`
2. **Local-Only:** Database content, secrets, PII data - requires external backup

**Key Insight:** PostgreSQL stores both application data AND RAG embeddings. One backup protects both.

---

## Data Categories

### LOCAL-ONLY (At Risk on Hardware Failure)

| Category | Location | Risk | Recovery Path |
|----------|----------|------|---------------|
| **PostgreSQL data** | Docker volume `postgres_data` | CRITICAL | Manual backup/restore |
| **PostgreSQL (dev)** | Docker volume `postgres_local_data` | CRITICAL | Manual backup/restore |
| **Redis cache** | Docker volume `redis_data` | LOW | Regenerates on startup |
| **RAG embeddings** | PostgreSQL `rag_documents` table | MEDIUM | Re-ingest from synced docs |
| **Database backups** | `backups/*.sql` | MEDIUM | External backup needed |
| **Environment secrets** | `.env`, `secrets/` | CRITICAL | Password manager / vault |
| **Real PII data** | `docs/data/*.json` | CRITICAL | Airtable source-of-truth |
| **Build artifacts** | `node_modules/`, `.next/`, `__pycache__/` | NONE | Rebuild from deps |
| **Celery scheduler** | `celerybeat-schedule` | NONE | Regenerates |
| **Logs** | `*.log`, `.antigravity/logs/` | LOW | Ephemeral by design |

### SYNCED (Recoverable from Git)

| Category | Location | Notes |
|----------|----------|-------|
| **Application code** | `backend/`, `frontend/`, `mcp-server/` | Full codebase |
| **Database schema** | `backend/alembic/versions/` | Migrations rebuild structure |
| **Config templates** | `.env.example`, `docker-compose*.yml` | Infrastructure-as-code |
| **Documentation** | `docs/` (except `docs/data/*.json`) | All sanitized docs |
| **PAI governance** | `.claude/` | Agent specs, skills, governance |
| **Tests** | `backend/tests/`, `frontend/__tests__/` | Full test suite |
| **CI/CD pipelines** | `.github/workflows/` | GitHub Actions |
| **RAG source docs** | `docs/rag-knowledge/` | Can re-ingest after recovery |

---

## Docker Volume Architecture

### Production (`docker-compose.yml`)
```yaml
volumes:
  postgres_data:       # PostgreSQL persistence
  redis_data:          # Redis persistence (cache/broker)
```

### Local Development (`docker-compose.local.yml`)
```yaml
volumes:
  postgres_local_data:  # Separate from production
  redis_local_data:     # Separate from production
  backend_local_venv:   # Python virtual environment
```

**Key Point:** Local and production use DIFFERENT volume names. Data doesn't cross-contaminate.

---

## Backup Recommendations

### Critical (Must Backup Externally)

| Item | Backup Method | Frequency |
|------|---------------|-----------|
| **PostgreSQL** | `pg_dump` to external storage | Daily |
| **`.env` secrets** | Password manager (1Password, Vault) | On change |
| **`secrets/` directory** | Password manager | On change |
| **PII source data** | Airtable is source-of-truth | N/A |

### Backup Script Example
```bash
#!/bin/bash
# backup-db.sh - Run daily via cron

BACKUP_DIR="/path/to/external/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec scheduler-local-db pg_dump -U scheduler residency_scheduler \
  > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Keep last 7 days
find "$BACKUP_DIR" -name "db_backup_*.sql" -mtime +7 -delete

echo "Backup complete: db_backup_$TIMESTAMP.sql"
```

### Low Priority (Regenerates)

| Item | Why No Backup Needed |
|------|---------------------|
| Redis cache | Celery tasks regenerate |
| Build artifacts | `npm install` / `pip install` |
| RAG embeddings | Re-ingest from synced docs |
| Celery scheduler | Rebuilds on startup |

---

## Disaster Recovery Procedure

### Scenario: Complete Hardware Failure

#### Step 1: Clone from Sacred Timeline
```bash
git clone https://github.com/[org]/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

#### Step 2: Restore Secrets
```bash
# From password manager or secure backup
cp /path/to/backup/.env .env
mkdir -p secrets
cp /path/to/backup/secrets/* secrets/
```

#### Step 3: Start Infrastructure
```bash
# Start all containers (creates fresh volumes)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Wait for healthy status
docker compose ps
```

#### Step 4: Run Migrations
```bash
# Rebuild database schema from migrations
docker exec scheduler-local-backend alembic upgrade head
```

#### Step 5: Restore Database Content
```bash
# If you have a backup
cat /path/to/backup/db_backup_LATEST.sql | \
  docker exec -i scheduler-local-db psql -U scheduler residency_scheduler
```

#### Step 6: Re-ingest RAG Knowledge Base
```bash
# RAG source docs are in git - just re-ingest
docker exec scheduler-local-backend python -c "
from app.tasks.rag_tasks import ingest_knowledge_base
import asyncio
asyncio.run(ingest_knowledge_base())
"
```

#### Step 7: Verify Recovery
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check MCP tools
curl http://localhost:8081/health
```

---

## What You Lose Without Backup

### If No Database Backup
- All schedule assignments
- All resident/faculty records
- All absence records
- All swap history
- All activity logs

**Recovery:** Re-import from Airtable or manual entry

### If No Secrets Backup
- Cannot authenticate (no JWT secret)
- Cannot connect to external services

**Recovery:** Generate new secrets, update integrations

### If No PII Mapping
- Cannot de-anonymize sanitized data
- Must re-create mappings from source

**Recovery:** Re-export from Airtable with new mappings

---

## Security: What's Gitignored

The following patterns are in `.gitignore` to prevent accidental commits:

```gitignore
# Secrets
.env
.env.local
secrets/

# Database
*.sql
*.dump
backups/

# PII Data
docs/data/*.json
docs/data/*.csv
!docs/data/sanitized_*.json
*.mapping.json

# Build artifacts
node_modules/
.next/
__pycache__/
```

**OPSEC Note:** All `.sql` files contain resident/faculty names and schedule assignments. NEVER commit these.

---

## Quick Reference

### Check What's Synced
```bash
git status --porcelain
```

### Check Volume Sizes
```bash
docker system df -v | grep -E "postgres|redis"
```

### Manual Database Backup
```bash
docker exec scheduler-local-db pg_dump -U scheduler residency_scheduler > backup.sql
```

### Manual Database Restore
```bash
cat backup.sql | docker exec -i scheduler-local-db psql -U scheduler residency_scheduler
```

### Verify RAG Health
```bash
curl http://localhost:8000/api/rag/health
```

---

## Related Documentation

- `docs/architecture/decisions/ADR-007-monorepo-docker-compose.md` - Docker architecture
- `docs/architecture/database.md` - Database schema
- `docs/development/DOCKER_WORKAROUNDS.md` - Docker troubleshooting
- `docs/security/PHI_EXPOSURE_AUDIT.md` - PII handling requirements

---

*This document should be updated when backup procedures or volume configurations change.*
