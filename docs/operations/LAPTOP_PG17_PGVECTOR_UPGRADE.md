# Laptop Upgrade Runbook: PostgreSQL 15 -> 17 + pgvector

**Goal:** Restore native RAG support on laptop by aligning with Mini (`PG17 + pgvector`).

## Preconditions

- Homebrew installed.
- Current local DB can be stopped briefly.
- Backup required before migration.

## 1. Snapshot Existing PG15 Data

```bash
# Stop app services that write to DB
./scripts/stop-native.sh

# Ensure PG15 is running long enough for dump
brew services start postgresql@15

# Full logical backup
pg_dumpall -h localhost > ~/pg15_backup_$(date +%Y%m%d_%H%M%S).sql
```

## 2. Install PG17 + pgvector

```bash
brew install postgresql@17 pgvector
brew services stop postgresql@15
brew services start postgresql@17
```

## 3. Recreate role + database + extension

```bash
createuser -s scheduler || true
psql -h localhost -d postgres -c "ALTER USER scheduler PASSWORD 'scheduler';"
createdb -h localhost -O scheduler residency_scheduler || true
psql -h localhost -d residency_scheduler -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 4. Restore data and run migrations

```bash
# Optional: restore full PG15 dump into PG17
psql -h localhost -d postgres < ~/pg15_backup_<timestamp>.sql

# Ensure schema is current
cd backend
.venv/bin/alembic upgrade head
```

## 5. Validate parity

```bash
# Check pgvector installed
psql -h localhost -d residency_scheduler -tAc "SELECT extversion FROM pg_extension WHERE extname='vector';"

# Start native stack
cd ..
./scripts/start-native.sh --bootstrap

# Validate health
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/rag/health
```

Expected outcome:

- backend healthy
- rag health no longer extension-erroring
- RAG ingest/retrieve routes functional

## Rollback

If issues occur:

```bash
./scripts/stop-native.sh --all
brew services start postgresql@15
# restore from backup if needed
psql -h localhost -d postgres < ~/pg15_backup_<timestamp>.sql
```

## Notes

- If PG15 must remain primary locally, use Docker `pgvector/pgvector:pg15` for RAG-only workflows.
- Keep only one local PostgreSQL service active on port 5432 at a time.
