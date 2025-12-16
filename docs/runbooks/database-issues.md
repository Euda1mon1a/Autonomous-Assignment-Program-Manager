# Runbook: Database Issues

**Alert Names:** `PostgreSQLDown`, `HighDatabaseConnections`, `DatabaseSlowQueries`
**Severity:** Critical/Warning
**Service:** Database

## Description

These alerts fire when PostgreSQL database experiences issues:
- Service unavailable
- Connection pool exhaustion
- Slow query performance
- Replication lag (if applicable)

## Impact

- Application cannot read/write data
- Schedule generation fails
- Users see errors or timeouts
- Data integrity at risk during recovery

## Quick Diagnosis

```bash
# 1. Check database container status
docker compose ps db

# 2. Check if PostgreSQL is accepting connections
docker compose exec db pg_isready -U scheduler

# 3. Check database logs
docker compose logs --tail=100 db

# 4. Check connection count
docker compose exec db psql -U scheduler -c \
  "SELECT count(*) as connections FROM pg_stat_activity;"

# 5. Check long-running queries
docker compose exec db psql -U scheduler -c \
  "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND query_start < now() - interval '5 minutes';"
```

## Resolution Steps

### Database Unavailable

**Step 1: Verify container status**
```bash
docker compose ps db
```

**If stopped, restart:**
```bash
docker compose up -d db
docker compose logs -f db
```

**Step 2: Check disk space**
```bash
docker compose exec db df -h /var/lib/postgresql/data
```

**If disk full:**
```bash
# Clean up WAL files (CAUTION: verify backup first)
docker compose exec db psql -U scheduler -c "SELECT pg_switch_wal();"

# Clean old transaction logs
docker compose exec db find /var/lib/postgresql/data/pg_wal -mtime +7 -delete
```

### High Connection Count

**Step 1: Identify connections**
```bash
docker compose exec db psql -U scheduler -c \
  "SELECT client_addr, usename, state, count(*)
   FROM pg_stat_activity
   GROUP BY client_addr, usename, state
   ORDER BY count DESC;"
```

**Step 2: Kill idle connections if needed**
```bash
docker compose exec db psql -U scheduler -c \
  "SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
   AND query_start < now() - interval '30 minutes';"
```

**Step 3: Increase connection limit (if recurring)**
Edit `postgresql.conf`:
```
max_connections = 200
```

### Slow Queries

**Step 1: Identify slow queries**
```bash
docker compose exec db psql -U scheduler -c \
  "SELECT query, calls, mean_time, total_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;"
```

**Step 2: Analyze query plans**
```bash
docker compose exec db psql -U scheduler -c \
  "EXPLAIN ANALYZE <slow_query_here>;"
```

**Step 3: Common fixes**
- Add missing indexes
- Update table statistics: `ANALYZE table_name;`
- Vacuum tables: `VACUUM ANALYZE;`

### Connection Pool Exhaustion

**Step 1: Check application pool settings**
See `backend/app/db/session.py`:
- `pool_size`: Base connections
- `max_overflow`: Burst connections

**Step 2: Adjust pool settings**
```bash
# In .env
DB_POOL_SIZE=15
DB_POOL_MAX_OVERFLOW=30
```

**Step 3: Restart backend**
```bash
docker compose restart backend
```

## Recovery Verification

```bash
# Verify database is healthy
docker compose exec db pg_isready -U scheduler

# Check backend can connect
curl http://localhost:8000/health

# Verify data integrity
docker compose exec db psql -U scheduler -c \
  "SELECT count(*) FROM people; SELECT count(*) FROM assignments;"
```

## Backup Procedures

**Before major changes, always backup:**
```bash
# Quick backup
docker compose exec db pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

# See full backup procedures
cat docs/admin-manual/backup-restore.md
```

## Escalation

| Timeframe | Action |
|-----------|--------|
| 0-5 min | Attempt restart |
| 5-15 min | Check logs, apply quick fixes |
| 15-30 min | Escalate to DBA/team lead |
| 30+ min | Consider failover/restore from backup |

## Related Alerts

- `APIServiceDown`
- `HighLatencyP95`
- `BackupFailed`

---

*Last Updated: December 2024*
