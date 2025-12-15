# Database Backup and Restore Procedures

## Overview

This guide provides comprehensive procedures for backing up and restoring the Residency Scheduler database. Regular backups are essential for disaster recovery, compliance (ACGME audit requirements), and business continuity.

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Manual Backup Procedures](#manual-backup-procedures)
3. [Automated Backup Setup](#automated-backup-setup)
4. [Restore Procedures](#restore-procedures)
5. [Point-in-Time Recovery](#point-in-time-recovery)
6. [Backup Verification](#backup-verification)
7. [Off-Site Storage](#off-site-storage)
8. [Disaster Recovery Plan](#disaster-recovery-plan)
9. [Troubleshooting](#troubleshooting)

---

## Backup Strategy

### Backup Types

| Type | Frequency | Retention | Use Case |
|------|-----------|-----------|----------|
| Full | Daily | 30 days | Complete recovery |
| Incremental | Hourly | 7 days | Point-in-time recovery |
| Transaction Log | Continuous | 24 hours | Minimal data loss recovery |

### Recommended Schedule

| Backup Type | Schedule | Time |
|-------------|----------|------|
| Full backup | Daily | 02:00 AM |
| Configuration backup | Weekly | Sunday 03:00 AM |
| Test restore | Monthly | First Sunday |

### Retention Policy

| Data Type | Retention Period | Reason |
|-----------|------------------|--------|
| Daily backups | 30 days | Operational recovery |
| Weekly backups | 3 months | Short-term archive |
| Monthly backups | 1 year | Medium-term archive |
| Annual backups | 7 years | ACGME compliance |

---

## Manual Backup Procedures

### Docker Environment

#### Full Database Backup

```bash
# Create backup directory
mkdir -p /opt/backups/residency-scheduler

# Run pg_dump
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --format=custom \
  --compress=9 \
  > /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).dump

# Verify backup was created
ls -lh /opt/backups/residency-scheduler/
```

#### SQL Format Backup (Human-Readable)

```bash
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --format=plain \
  > /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).sql
```

#### Compressed SQL Backup

```bash
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --format=plain | gzip \
  > /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Backup Specific Tables

```bash
# Backup only user and audit data
docker compose exec -T db pg_dump \
  -U scheduler \
  -d residency_scheduler \
  --table=users \
  --table=audit_logs \
  > /opt/backups/residency-scheduler/users_audit_$(date +%Y%m%d).sql
```

### Manual Installation Environment

#### Full Database Backup

```bash
# As postgres user or with appropriate credentials
pg_dump \
  -U scheduler \
  -h localhost \
  -d residency_scheduler \
  --format=custom \
  --compress=9 \
  -f /opt/backups/residency-scheduler/backup_$(date +%Y%m%d_%H%M%S).dump
```

#### Using Environment File

```bash
# Create .pgpass for non-interactive authentication
echo "localhost:5432:residency_scheduler:scheduler:your_password" > ~/.pgpass
chmod 600 ~/.pgpass

# Backup without password prompt
pg_dump -U scheduler -h localhost -d residency_scheduler \
  --format=custom > backup.dump
```

---

## Automated Backup Setup

### Backup Script

Create `/opt/residency-scheduler/scripts/backup.sh`:

```bash
#!/bin/bash
#
# Residency Scheduler Database Backup Script
# Run via cron: 0 2 * * * /opt/residency-scheduler/scripts/backup.sh
#

set -e

# Configuration
BACKUP_DIR="/opt/backups/residency-scheduler"
RETENTION_DAYS=30
DB_NAME="residency_scheduler"
DB_USER="scheduler"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/residency-scheduler/backup.log"

# Docker or direct PostgreSQL
USE_DOCKER=true
DOCKER_COMPOSE_DIR="/opt/residency-scheduler"

# Notification settings (optional)
NOTIFY_EMAIL="admin@hospital.org"
NOTIFY_ON_FAILURE=true

# Functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

notify_failure() {
    if [ "$NOTIFY_ON_FAILURE" = true ] && [ -n "$NOTIFY_EMAIL" ]; then
        echo "Backup failed: $1" | mail -s "Residency Scheduler Backup Failed" "$NOTIFY_EMAIL"
    fi
}

# Create backup directory if needed
mkdir -p "$BACKUP_DIR"

log "Starting backup..."

# Create backup
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

# Verify backup
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    log "ERROR: Backup file is missing or empty"
    notify_failure "Backup file is missing or empty"
    exit 1
fi

BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
log "Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Create checksum
md5sum "$BACKUP_FILE" > "${BACKUP_FILE}.md5"
log "Checksum created: ${BACKUP_FILE}.md5"

# Clean old backups
log "Cleaning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "backup_*.dump" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "backup_*.md5" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.dump" | wc -l)
log "Backup complete. Total backups retained: $BACKUP_COUNT"

# Optional: Copy to remote storage
# aws s3 cp "$BACKUP_FILE" s3://your-bucket/backups/
# gsutil cp "$BACKUP_FILE" gs://your-bucket/backups/

exit 0
```

Make executable:

```bash
chmod +x /opt/residency-scheduler/scripts/backup.sh
```

### Cron Configuration

```bash
# Edit crontab
crontab -e

# Add backup schedule
# Daily full backup at 2 AM
0 2 * * * /opt/residency-scheduler/scripts/backup.sh >> /var/log/residency-scheduler/backup-cron.log 2>&1

# Weekly configuration backup on Sunday at 3 AM
0 3 * * 0 /opt/residency-scheduler/scripts/backup-config.sh >> /var/log/residency-scheduler/backup-cron.log 2>&1
```

### Configuration Backup Script

Create `/opt/residency-scheduler/scripts/backup-config.sh`:

```bash
#!/bin/bash
#
# Configuration backup script
#

set -e

BACKUP_DIR="/opt/backups/residency-scheduler/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/residency-scheduler"

mkdir -p "$BACKUP_DIR"

# Create tarball of configuration files
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

# Clean old config backups (keep 12 weeks)
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +84 -delete
```

---

## Restore Procedures

### Pre-Restore Checklist

- [ ] Verify backup file integrity
- [ ] Confirm target environment
- [ ] Notify users of downtime
- [ ] Stop application services
- [ ] Document current database state

### Docker Environment Restore

#### Stop Services

```bash
cd /opt/residency-scheduler
docker compose stop backend frontend
```

#### Restore Database

```bash
# Method 1: Custom format (.dump)
docker compose exec -T db pg_restore \
  -U scheduler \
  -d residency_scheduler \
  --clean \
  --if-exists \
  < /opt/backups/residency-scheduler/backup_20241215_020000.dump

# Method 2: SQL format (.sql)
cat /opt/backups/residency-scheduler/backup_20241215_020000.sql \
  | docker compose exec -T db psql -U scheduler -d residency_scheduler

# Method 3: Compressed SQL (.sql.gz)
gunzip -c /opt/backups/residency-scheduler/backup_20241215_020000.sql.gz \
  | docker compose exec -T db psql -U scheduler -d residency_scheduler
```

#### Restart Services

```bash
docker compose start backend frontend
docker compose ps
```

### Manual Installation Restore

#### Stop Services

```bash
sudo systemctl stop residency-backend
```

#### Restore Database

```bash
# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS residency_scheduler;"
sudo -u postgres psql -c "CREATE DATABASE residency_scheduler OWNER scheduler;"

# Restore from custom format
pg_restore \
  -U scheduler \
  -h localhost \
  -d residency_scheduler \
  /opt/backups/residency-scheduler/backup_20241215_020000.dump

# Or from SQL format
psql -U scheduler -h localhost -d residency_scheduler \
  < /opt/backups/residency-scheduler/backup_20241215_020000.sql
```

#### Run Migrations

```bash
cd /opt/residency-scheduler/backend
./venv/bin/alembic upgrade head
```

#### Restart Services

```bash
sudo systemctl start residency-backend
sudo systemctl status residency-backend
```

### Partial Restore (Specific Tables)

```bash
# Restore only specific tables from backup
pg_restore \
  -U scheduler \
  -h localhost \
  -d residency_scheduler \
  --table=users \
  --data-only \
  backup.dump
```

---

## Point-in-Time Recovery

### Enable WAL Archiving

Edit PostgreSQL configuration (`postgresql.conf`):

```ini
# Enable WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'cp %p /opt/backups/wal_archive/%f'

# WAL settings
max_wal_senders = 3
wal_keep_size = 1GB
```

Create archive directory:

```bash
mkdir -p /opt/backups/wal_archive
chown postgres:postgres /opt/backups/wal_archive
chmod 700 /opt/backups/wal_archive
```

### Perform Point-in-Time Recovery

```bash
# 1. Stop PostgreSQL
sudo systemctl stop postgresql

# 2. Back up current data directory
mv /var/lib/postgresql/15/main /var/lib/postgresql/15/main.old

# 3. Restore base backup
pg_basebackup \
  -D /var/lib/postgresql/15/main \
  -Fp -Xs -P

# 4. Create recovery configuration
cat > /var/lib/postgresql/15/main/postgresql.auto.conf << EOF
restore_command = 'cp /opt/backups/wal_archive/%f %p'
recovery_target_time = '2024-12-15 14:30:00'
recovery_target_action = 'promote'
EOF

# 5. Create recovery signal
touch /var/lib/postgresql/15/main/recovery.signal

# 6. Start PostgreSQL
sudo systemctl start postgresql
```

---

## Backup Verification

### Verify Backup Integrity

```bash
# Check custom format backup
pg_restore --list backup.dump > /dev/null && echo "Backup is valid"

# Verify checksum
md5sum -c backup.dump.md5
```

### Test Restore (Monthly)

```bash
#!/bin/bash
# Test restore script - run monthly

TEST_DB="residency_scheduler_test"
LATEST_BACKUP=$(ls -t /opt/backups/residency-scheduler/backup_*.dump | head -1)

echo "Testing restore of: $LATEST_BACKUP"

# Create test database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $TEST_DB;"
sudo -u postgres psql -c "CREATE DATABASE $TEST_DB;"

# Restore
pg_restore -U scheduler -h localhost -d "$TEST_DB" "$LATEST_BACKUP"

# Verify data
PEOPLE_COUNT=$(psql -U scheduler -h localhost -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM people;")
echo "People records restored: $PEOPLE_COUNT"

# Cleanup
sudo -u postgres psql -c "DROP DATABASE $TEST_DB;"

echo "Test restore completed successfully"
```

### Automated Verification

Add to backup script:

```bash
# Verify backup after creation
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

## Off-Site Storage

### AWS S3 Storage

```bash
# Install AWS CLI
apt install awscli

# Configure credentials
aws configure

# Upload backup
aws s3 cp /opt/backups/residency-scheduler/backup_20241215.dump \
  s3://your-bucket/residency-scheduler/backups/

# Sync backup directory
aws s3 sync /opt/backups/residency-scheduler/ \
  s3://your-bucket/residency-scheduler/backups/ \
  --exclude "*.tmp"
```

### Google Cloud Storage

```bash
# Install gsutil
apt install google-cloud-cli

# Authenticate
gcloud auth login

# Upload backup
gsutil cp /opt/backups/residency-scheduler/backup_20241215.dump \
  gs://your-bucket/residency-scheduler/backups/
```

### Encrypted Off-Site Backup

```bash
# Encrypt before upload
gpg --symmetric --cipher-algo AES256 \
  -o backup_encrypted.dump.gpg \
  backup.dump

# Upload encrypted file
aws s3 cp backup_encrypted.dump.gpg s3://your-bucket/backups/

# Decrypt after download
gpg --decrypt backup_encrypted.dump.gpg > backup_restored.dump
```

---

## Disaster Recovery Plan

### Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Hardware failure | 4 hours | 1 hour |
| Data corruption | 2 hours | 24 hours |
| Complete site loss | 24 hours | 24 hours |

### Recovery Procedures

#### Level 1: Service Restart

```bash
# Restart services
docker compose restart

# Or for manual installation
sudo systemctl restart residency-backend nginx
```

#### Level 2: Restore from Latest Backup

1. Stop services
2. Restore database from latest backup
3. Verify data integrity
4. Restart services
5. Notify users

#### Level 3: Full System Recovery

1. Provision new infrastructure
2. Install base system
3. Deploy application
4. Restore database from off-site backup
5. Restore configuration
6. Update DNS records
7. Verify functionality
8. Notify users

### Emergency Contacts

| Role | Contact | Phone |
|------|---------|-------|
| DBA | TBD | TBD |
| System Admin | TBD | TBD |
| Application Owner | TBD | TBD |

---

## Troubleshooting

### Common Issues

#### Backup Fails with Permission Denied

```bash
# Fix backup directory permissions
sudo chown -R $USER:$USER /opt/backups/residency-scheduler
sudo chmod 755 /opt/backups/residency-scheduler
```

#### Restore Fails: Database in Use

```bash
# Terminate active connections
sudo -u postgres psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'residency_scheduler' AND pid <> pg_backend_pid();"
```

#### Restore Fails: Version Mismatch

```bash
# Check PostgreSQL versions
pg_dump --version
pg_restore --version

# Upgrade PostgreSQL if needed
```

#### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean old backups
find /opt/backups -name "*.dump" -mtime +30 -delete

# Clean Docker volumes
docker system prune -a
```

### Backup Monitoring

```bash
# Check backup age
LAST_BACKUP=$(ls -t /opt/backups/residency-scheduler/backup_*.dump | head -1)
BACKUP_AGE=$((($(date +%s) - $(stat -c %Y "$LAST_BACKUP")) / 3600))
echo "Last backup: $BACKUP_AGE hours ago"

if [ $BACKUP_AGE -gt 24 ]; then
    echo "WARNING: Backup is more than 24 hours old!"
fi
```

---

## Backup Checklist

### Daily

- [ ] Verify automated backup completed
- [ ] Check backup size is reasonable
- [ ] Verify backup logs for errors

### Weekly

- [ ] Review backup retention
- [ ] Verify off-site sync completed
- [ ] Check storage capacity

### Monthly

- [ ] Test restore procedure
- [ ] Verify backup encryption
- [ ] Update disaster recovery documentation
- [ ] Review and rotate credentials

### Annually

- [ ] Test full disaster recovery
- [ ] Review and update retention policy
- [ ] Archive annual backups

---

*Last Updated: December 2024*
