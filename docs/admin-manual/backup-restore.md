***REMOVED*** Database Backup and Restore Procedures

***REMOVED******REMOVED*** Overview

This guide provides comprehensive procedures for backing up and restoring the Residency Scheduler database. Regular backups are essential for disaster recovery, compliance (ACGME audit requirements), and business continuity.

***REMOVED******REMOVED*** Table of Contents

1. [Backup Strategy](***REMOVED***backup-strategy)
2. [Manual Backup Procedures](***REMOVED***manual-backup-procedures)
3. [Automated Backup Setup](***REMOVED***automated-backup-setup)
4. [Restore Procedures](***REMOVED***restore-procedures)
5. [Point-in-Time Recovery](***REMOVED***point-in-time-recovery)
6. [Backup Verification](***REMOVED***backup-verification)
7. [Off-Site Storage](***REMOVED***off-site-storage)
8. [Disaster Recovery Plan](***REMOVED***disaster-recovery-plan)
9. [Troubleshooting](***REMOVED***troubleshooting)

---

***REMOVED******REMOVED*** Backup Strategy

***REMOVED******REMOVED******REMOVED*** Backup Types

| Type | Frequency | Retention | Use Case |
|------|-----------|-----------|----------|
| Full | Daily | 30 days | Complete recovery |
| Incremental | Hourly | 7 days | Point-in-time recovery |
| Transaction Log | Continuous | 24 hours | Minimal data loss recovery |

***REMOVED******REMOVED******REMOVED*** Recommended Schedule

| Backup Type | Schedule | Time |
|-------------|----------|------|
| Full backup | Daily | 02:00 AM |
| Configuration backup | Weekly | Sunday 03:00 AM |
| Test restore | Monthly | First Sunday |

***REMOVED******REMOVED******REMOVED*** Retention Policy

| Data Type | Retention Period | Reason |
|-----------|------------------|--------|
| Daily backups | 30 days | Operational recovery |
| Weekly backups | 3 months | Short-term archive |
| Monthly backups | 1 year | Medium-term archive |
| Annual backups | 7 years | ACGME compliance |

---

***REMOVED******REMOVED*** Manual Backup Procedures

***REMOVED******REMOVED******REMOVED*** Docker Environment

***REMOVED******REMOVED******REMOVED******REMOVED*** Full Database Backup

```bash
***REMOVED*** Create backup directory
mkdir -p /opt/backups/residency-scheduler

***REMOVED*** Run pg_dump
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --format=custom \
  --compress=9 \
  > /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).dump

***REMOVED*** Verify backup was created
ls -lh /opt/backups/residency-scheduler/
```

***REMOVED******REMOVED******REMOVED******REMOVED*** SQL Format Backup (Human-Readable)

```bash
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --format=plain \
  > /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).sql
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Compressed SQL Backup

```bash
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --format=plain | gzip \
  > /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Backup Specific Tables

```bash
***REMOVED*** Backup only user and audit data
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --table=users \
  --table=audit_logs \
  > /opt/backups/residency-scheduler/users_audit_$(date +%Y%m%d).sql
```

***REMOVED******REMOVED******REMOVED*** Manual Installation Environment

***REMOVED******REMOVED******REMOVED******REMOVED*** Full Database Backup

```bash
***REMOVED*** As postgres user or with appropriate credentials
pg_dump \
  -U scheduler \
  -h localhost \
  -d residency_scheduler \
  --format=custom \
  --compress=9 \
  -f /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).dump
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Using Environment File

```bash
***REMOVED*** Create .pgpass for non-interactive authentication
echo "localhost:5432:residency_scheduler:scheduler:your_password" > ~/.pgpass
chmod 600 ~/.pgpass

***REMOVED*** Backup without password prompt
pg_dump -U scheduler -h localhost -d residency_scheduler \
  --format=custom > backup.dump
```

---

***REMOVED******REMOVED*** Automated Backup Setup

***REMOVED******REMOVED******REMOVED*** Backup Script

Create `/opt/residency-scheduler/scripts/backup.sh`:

```bash
***REMOVED***!/bin/bash
***REMOVED***
***REMOVED*** Residency Scheduler Database Backup Script
***REMOVED*** Run via cron: 0 2 * * * /opt/residency-scheduler/scripts/backup.sh
***REMOVED***

set -e

***REMOVED*** Configuration
BACKUP_DIR="/opt/backups/residency-scheduler"
RETENTION_DAYS=30
DB_NAME="residency_scheduler"
DB_USER="scheduler"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/residency-scheduler/backup.log"

***REMOVED*** Docker or direct PostgreSQL
USE_DOCKER=true
DOCKER_COMPOSE_DIR="/opt/residency-scheduler"

***REMOVED*** Notification settings (optional)
NOTIFY_EMAIL="admin@hospital.org"
NOTIFY_ON_FAILURE=true

***REMOVED*** Functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

notify_failure() {
    if [ "$NOTIFY_ON_FAILURE" = true ] && [ -n "$NOTIFY_EMAIL" ]; then
        echo "Backup failed: $1" | mail -s "Residency Scheduler Backup Failed" "$NOTIFY_EMAIL"
    fi
}

***REMOVED*** Create backup directory if needed
mkdir -p "$BACKUP_DIR"

log "Starting backup..."

***REMOVED*** Create backup
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.dump"

if [ "$USE_DOCKER" = true ]; then
    cd "$DOCKER_COMPOSE_DIR"
    docker compose exec -T db pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        > "$BACKUP_FILE"
else
    pg_dump \
        -U "$DB_USER" \
        -h localhost \
        -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        -f "$BACKUP_FILE"
fi

***REMOVED*** Verify backup
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    log "ERROR: Backup file is missing or empty"
    notify_failure "Backup file is missing or empty"
    exit 1
fi

BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
log "Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

***REMOVED*** Create checksum
md5sum "$BACKUP_FILE" > "${BACKUP_FILE}.md5"
log "Checksum created: ${BACKUP_FILE}.md5"

***REMOVED*** Clean old backups
log "Cleaning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "backup_*.dump" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "backup_*.md5" -mtime +$RETENTION_DAYS -delete

***REMOVED*** Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.dump" | wc -l)
log "Backup complete. Total backups retained: $BACKUP_COUNT"

***REMOVED*** Optional: Copy to remote storage
***REMOVED*** aws s3 cp "$BACKUP_FILE" s3://your-bucket/backups/
***REMOVED*** gsutil cp "$BACKUP_FILE" gs://your-bucket/backups/

exit 0
```

Make executable:

```bash
chmod +x /opt/residency-scheduler/scripts/backup.sh
```

***REMOVED******REMOVED******REMOVED*** Cron Configuration

```bash
***REMOVED*** Edit crontab
crontab -e

***REMOVED*** Add backup schedule
***REMOVED*** Daily full backup at 2 AM
0 2 * * * /opt/residency-scheduler/scripts/backup.sh >> /var/log/residency-scheduler/backup-cron.log 2>&1

***REMOVED*** Weekly configuration backup on Sunday at 3 AM
0 3 * * 0 /opt/residency-scheduler/scripts/backup-config.sh >> /var/log/residency-scheduler/backup-cron.log 2>&1
```

***REMOVED******REMOVED******REMOVED*** Configuration Backup Script

Create `/opt/residency-scheduler/scripts/backup-config.sh`:

```bash
***REMOVED***!/bin/bash
***REMOVED***
***REMOVED*** Configuration backup script
***REMOVED***

set -e

BACKUP_DIR="/opt/backups/residency-scheduler/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/residency-scheduler"

mkdir -p "$BACKUP_DIR"

***REMOVED*** Create tarball of configuration files
tar -czf "$BACKUP_DIR/config_${TIMESTAMP}.tar.gz" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    "$APP_DIR/.env" \
    "$APP_DIR/docker-compose.yml" \
    "$APP_DIR/docker-compose.dev.yml" \
    /etc/nginx/sites-available/residency-scheduler \
    /etc/systemd/system/residency-backend.service \
    2>/dev/null || true

echo "Configuration backup created: $BACKUP_DIR/config_${TIMESTAMP}.tar.gz"

***REMOVED*** Clean old config backups (keep 12 weeks)
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +84 -delete
```

---

***REMOVED******REMOVED*** Restore Procedures

***REMOVED******REMOVED******REMOVED*** Pre-Restore Checklist

- [ ] Verify backup file integrity
- [ ] Confirm target environment
- [ ] Notify users of downtime
- [ ] Stop application services
- [ ] Document current database state

***REMOVED******REMOVED******REMOVED*** Docker Environment Restore

***REMOVED******REMOVED******REMOVED******REMOVED*** Stop Services

```bash
cd /opt/residency-scheduler
docker compose stop backend frontend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Restore Database

```bash
***REMOVED*** Method 1: Custom format (.dump)
docker compose exec -T db pg_restore \
  -U scheduler \
  -d residency_scheduler \
  --clean \
  --if-exists \
  < /opt/backups/residency-scheduler/backup_20241215_020000.dump

***REMOVED*** Method 2: SQL format (.sql)
cat /opt/backups/residency-scheduler/backup_20241215_020000.sql \
  | docker compose exec -T db psql -U scheduler -d residency_scheduler

***REMOVED*** Method 3: Compressed SQL (.sql.gz)
gunzip -c /opt/backups/residency-scheduler/backup_20241215_020000.sql.gz \
  | docker compose exec -T db psql -U scheduler -d residency_scheduler
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Restart Services

```bash
docker compose start backend frontend
docker compose ps
```

***REMOVED******REMOVED******REMOVED*** Manual Installation Restore

***REMOVED******REMOVED******REMOVED******REMOVED*** Stop Services

```bash
sudo systemctl stop residency-backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Restore Database

```bash
***REMOVED*** Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS residency_scheduler;"
sudo -u postgres psql -c "CREATE DATABASE residency_scheduler OWNER scheduler;"

***REMOVED*** Restore from custom format
pg_restore \
  -U scheduler \
  -h localhost \
  -d residency_scheduler \
  /opt/backups/residency-scheduler/backup_20241215_020000.dump

***REMOVED*** Or from SQL format
psql -U scheduler -h localhost -d residency_scheduler \
  < /opt/backups/residency-scheduler/backup_20241215_020000.sql
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Run Migrations

```bash
cd /opt/residency-scheduler/backend
./venv/bin/alembic upgrade head
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Restart Services

```bash
sudo systemctl start residency-backend
sudo systemctl status residency-backend
```

***REMOVED******REMOVED******REMOVED*** Partial Restore (Specific Tables)

```bash
***REMOVED*** Restore only specific tables from backup
pg_restore \
  -U scheduler \
  -h localhost \
  -d residency_scheduler \
  --table=users \
  --data-only \
  backup.dump
```

---

***REMOVED******REMOVED*** Point-in-Time Recovery

***REMOVED******REMOVED******REMOVED*** Enable WAL Archiving

Edit PostgreSQL configuration (`postgresql.conf`):

```ini
***REMOVED*** Enable WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'cp %p /opt/backups/wal_archive/%f'

***REMOVED*** WAL settings
max_wal_senders = 3
wal_keep_size = 1GB
```

Create archive directory:

```bash
mkdir -p /opt/backups/wal_archive
chown postgres:postgres /opt/backups/wal_archive
chmod 700 /opt/backups/wal_archive
```

***REMOVED******REMOVED******REMOVED*** Perform Point-in-Time Recovery

```bash
***REMOVED*** 1. Stop PostgreSQL
sudo systemctl stop postgresql

***REMOVED*** 2. Back up current data directory
mv /var/lib/postgresql/15/main /var/lib/postgresql/15/main.old

***REMOVED*** 3. Restore base backup
pg_basebackup \
  -D /var/lib/postgresql/15/main \
  -Fp -Xs -P

***REMOVED*** 4. Create recovery configuration
cat > /var/lib/postgresql/15/main/postgresql.auto.conf << EOF
restore_command = 'cp /opt/backups/wal_archive/%f %p'
recovery_target_time = '2024-12-15 14:30:00'
recovery_target_action = 'promote'
EOF

***REMOVED*** 5. Create recovery signal
touch /var/lib/postgresql/15/main/recovery.signal

***REMOVED*** 6. Start PostgreSQL
sudo systemctl start postgresql
```

---

***REMOVED******REMOVED*** Backup Verification

***REMOVED******REMOVED******REMOVED*** Verify Backup Integrity

```bash
***REMOVED*** Check custom format backup
pg_restore --list backup.dump > /dev/null && echo "Backup is valid"

***REMOVED*** Verify checksum
md5sum -c backup.dump.md5
```

***REMOVED******REMOVED******REMOVED*** Test Restore (Monthly)

```bash
***REMOVED***!/bin/bash
***REMOVED*** Test restore script - run monthly

TEST_DB="residency_scheduler_test"
LATEST_BACKUP=$(ls -t /opt/backups/residency-scheduler/backup_*.dump | head -1)

echo "Testing restore of: $LATEST_BACKUP"

***REMOVED*** Create test database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $TEST_DB;"
sudo -u postgres psql -c "CREATE DATABASE $TEST_DB;"

***REMOVED*** Restore
pg_restore -U scheduler -h localhost -d "$TEST_DB" "$LATEST_BACKUP"

***REMOVED*** Verify data
PEOPLE_COUNT=$(psql -U scheduler -h localhost -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM people;")
echo "People records restored: $PEOPLE_COUNT"

***REMOVED*** Cleanup
sudo -u postgres psql -c "DROP DATABASE $TEST_DB;"

echo "Test restore completed successfully"
```

***REMOVED******REMOVED******REMOVED*** Automated Verification

Add to backup script:

```bash
***REMOVED*** Verify backup after creation
echo "Verifying backup..."
if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
    log "Backup verification: PASSED"
else
    log "ERROR: Backup verification FAILED"
    notify_failure "Backup verification failed"
    exit 1
fi
```

---

***REMOVED******REMOVED*** Off-Site Storage

***REMOVED******REMOVED******REMOVED*** AWS S3 Storage

```bash
***REMOVED*** Install AWS CLI
apt install awscli

***REMOVED*** Configure credentials
aws configure

***REMOVED*** Upload backup
aws s3 cp /opt/backups/residency-scheduler/backup_20241215.dump \
  s3://your-bucket/residency-scheduler/backups/

***REMOVED*** Sync backup directory
aws s3 sync /opt/backups/residency-scheduler/ \
  s3://your-bucket/residency-scheduler/backups/ \
  --exclude "*.tmp"
```

***REMOVED******REMOVED******REMOVED*** Google Cloud Storage

```bash
***REMOVED*** Install gsutil
apt install google-cloud-cli

***REMOVED*** Authenticate
gcloud auth login

***REMOVED*** Upload backup
gsutil cp /opt/backups/residency-scheduler/backup_20241215.dump \
  gs://your-bucket/residency-scheduler/backups/
```

***REMOVED******REMOVED******REMOVED*** Encrypted Off-Site Backup

```bash
***REMOVED*** Encrypt before upload
gpg --symmetric --cipher-algo AES256 \
  -o backup_encrypted.dump.gpg \
  backup.dump

***REMOVED*** Upload encrypted file
aws s3 cp backup_encrypted.dump.gpg s3://your-bucket/backups/

***REMOVED*** Decrypt after download
gpg --decrypt backup_encrypted.dump.gpg > backup_restored.dump
```

---

***REMOVED******REMOVED*** Disaster Recovery Plan

***REMOVED******REMOVED******REMOVED*** Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Hardware failure | 4 hours | 1 hour |
| Data corruption | 2 hours | 24 hours |
| Complete site loss | 24 hours | 24 hours |

***REMOVED******REMOVED******REMOVED*** Recovery Procedures

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 1: Service Restart

```bash
***REMOVED*** Restart services
docker compose restart

***REMOVED*** Or for manual installation
sudo systemctl restart residency-backend nginx
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 2: Restore from Latest Backup

1. Stop services
2. Restore database from latest backup
3. Verify data integrity
4. Restart services
5. Notify users

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 3: Full System Recovery

1. Provision new infrastructure
2. Install base system
3. Deploy application
4. Restore database from off-site backup
5. Restore configuration
6. Update DNS records
7. Verify functionality
8. Notify users

***REMOVED******REMOVED******REMOVED*** Emergency Contacts

| Role | Contact | Phone |
|------|---------|-------|
| DBA | TBD | TBD |
| System Admin | TBD | TBD |
| Application Owner | TBD | TBD |

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Common Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** Backup Fails with Permission Denied

```bash
***REMOVED*** Fix backup directory permissions
sudo chown -R $USER:$USER /opt/backups/residency-scheduler
sudo chmod 755 /opt/backups/residency-scheduler
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Restore Fails: Database in Use

```bash
***REMOVED*** Terminate active connections
sudo -u postgres psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'residency_scheduler' AND pid <> pg_backend_pid();"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Restore Fails: Version Mismatch

```bash
***REMOVED*** Check PostgreSQL versions
pg_dump --version
pg_restore --version

***REMOVED*** Upgrade PostgreSQL if needed
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Out of Disk Space

```bash
***REMOVED*** Check disk usage
df -h

***REMOVED*** Clean old backups
find /opt/backups -name "*.dump" -mtime +30 -delete

***REMOVED*** Clean Docker volumes
docker system prune -a
```

***REMOVED******REMOVED******REMOVED*** Backup Monitoring

```bash
***REMOVED*** Check backup age
LAST_BACKUP=$(ls -t /opt/backups/residency-scheduler/backup_*.dump | head -1)
BACKUP_AGE=$((($(date +%s) - $(stat -c %Y "$LAST_BACKUP")) / 3600))
echo "Last backup: $BACKUP_AGE hours ago"

if [ $BACKUP_AGE -gt 24 ]; then
    echo "WARNING: Backup is more than 24 hours old!"
fi
```

---

***REMOVED******REMOVED*** Backup Checklist

***REMOVED******REMOVED******REMOVED*** Daily

- [ ] Verify automated backup completed
- [ ] Check backup size is reasonable
- [ ] Verify backup logs for errors

***REMOVED******REMOVED******REMOVED*** Weekly

- [ ] Review backup retention
- [ ] Verify off-site sync completed
- [ ] Check storage capacity

***REMOVED******REMOVED******REMOVED*** Monthly

- [ ] Test restore procedure
- [ ] Verify backup encryption
- [ ] Update disaster recovery documentation
- [ ] Review and rotate credentials

***REMOVED******REMOVED******REMOVED*** Annually

- [ ] Test full disaster recovery
- [ ] Review and update retention policy
- [ ] Archive annual backups

---

*Last Updated: December 2024*
