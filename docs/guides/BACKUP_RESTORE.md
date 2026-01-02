# Backup and Restore Guide

## Quick Backup

Run the full stack backup script:

```bash
# Basic backup (database + volumes + frontend)
./scripts/backup_full_stack.sh

# Include Redis data
./scripts/backup_full_stack.sh --include-redis

# Custom output directory
./scripts/backup_full_stack.sh --output-dir /path/to/backups
```

## Backup Contents

Each backup creates a timestamped folder with:

| Folder | Contents |
|--------|----------|
| `postgres/` | Compressed SQL dump + plain SQL |
| `volumes/` | Docker volume tarballs |
| `frontend/` | .next build + package-lock.json |
| `config_snapshot.json` | Git info, container state, DB stats |

## Restore Procedures

### 1. Restore Database Only

```bash
# From compressed backup
gunzip -c backups/full_TIMESTAMP/postgres/residency_scheduler_*.sql.gz | \
  docker compose -f docker-compose.local.yml exec -T db \
  psql -U scheduler -d residency_scheduler

# From plain SQL
docker compose -f docker-compose.local.yml exec -T db \
  psql -U scheduler -d residency_scheduler < backups/full_TIMESTAMP/postgres/*_plain.sql
```

### 2. Restore Docker Volume

```bash
# Stop containers first
docker compose -f docker-compose.local.yml down

# Restore volume
docker run --rm \
  -v scheduler-local_db_data:/target \
  -v $(pwd)/backups/full_TIMESTAMP/volumes:/backup \
  alpine sh -c "rm -rf /target/* && tar xzf /backup/db_volume_*.tar.gz -C /target"

# Restart
docker compose -f docker-compose.local.yml up -d
```

### 3. Full Stack Restore

```bash
# 1. Stop everything
docker compose -f docker-compose.local.yml down -v

# 2. Recreate volumes and restore
docker compose -f docker-compose.local.yml up -d db redis
sleep 10

# 3. Restore database
gunzip -c backups/full_TIMESTAMP/postgres/*.sql.gz | \
  docker compose -f docker-compose.local.yml exec -T db \
  psql -U scheduler -d residency_scheduler

# 4. Start remaining services
docker compose -f docker-compose.local.yml up -d
```

## Security Notes

> **⚠️ CRITICAL: Backups contain PHI (real names)**
> - Never commit backup files to git
> - Store securely with encryption
> - `backups/full_*` is in .gitignore

## Automated Backups

To schedule daily backups:

```bash
# Add to crontab (crontab -e)
0 2 * * * /path/to/project/scripts/backup_full_stack.sh >> /var/log/scheduler_backup.log 2>&1
```
