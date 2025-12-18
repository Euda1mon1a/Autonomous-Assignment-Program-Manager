# Backup & Restore

Data backup and recovery procedures.

---

## Automated Backups

The system creates daily automated backups via Celery.

### Backup Location

```
/backups/
├── daily/
│   ├── backup-2025-01-15.sql
│   └── backup-2025-01-14.sql
├── weekly/
│   └── backup-week-03.sql
└── monthly/
    └── backup-2025-01.sql
```

---

## Manual Backup

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres residency_scheduler > backup.sql

# Compressed backup
docker-compose exec db pg_dump -U postgres residency_scheduler | gzip > backup.sql.gz
```

### Full System Backup

```bash
# Stop services
docker-compose down

# Backup volumes
tar -czvf backup-full.tar.gz ./data

# Restart services
docker-compose up -d
```

---

## Restore Procedures

### Database Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U postgres residency_scheduler < backup.sql
```

### Full System Restore

```bash
# Stop services
docker-compose down

# Restore volumes
tar -xzvf backup-full.tar.gz

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

---

## Error Handling

The backup/restore system includes comprehensive error handling with custom exceptions.

### Exception Types

| Exception | Description |
|-----------|-------------|
| `BackupError` | Base exception for all backup failures |
| `BackupCreationError` | Failed to create backup |
| `BackupReadError` | Failed to read backup file |
| `BackupWriteError` | Failed to write backup file |
| `BackupNotFoundError` | Requested backup does not exist |
| `BackupValidationError` | Backup data validation failed |
| `BackupPermissionError` | Insufficient permissions |
| `BackupStorageError` | Storage-related issues (disk full, etc.) |
| `RestoreError` | Base exception for restore failures |
| `RestoreValidationError` | Restore data validation failed |
| `RestoreDataError` | Data integrity issues during restore |
| `RestorePermissionError` | Insufficient permissions for restore |
| `RestoreRollbackError` | Failed to rollback failed restore |

### Pre-Backup Validation

Before creating backups, the system validates:

1. **Disk Space**: Ensures minimum 100MB free space (configurable)
2. **Directory Permissions**: Checks read/write access to backup directory
3. **Backup Type**: Validates requested backup type is supported

### Logging

All backup/restore operations are logged at appropriate levels:

- **INFO**: Successful operations (backup created, restore completed)
- **WARNING**: Non-fatal issues (metadata save failed, but backup succeeded)
- **ERROR**: Operation failures with full context
- **DEBUG**: Detailed operation progress

```bash
# View backup logs
docker-compose logs backend | grep -i backup

# View restore logs
docker-compose logs backend | grep -i restore
```

---

## Backup Best Practices

!!! tip "Backup Recommendations"
    - Test restores regularly
    - Store backups off-site
    - Encrypt sensitive backups
    - Document restore procedures
    - Monitor disk space for backup storage
    - Set up alerts for backup failures
    - Maintain retention policies to manage storage

!!! warning "Pre-Restore Checklist"
    - Verify backup file integrity
    - Check available disk space
    - Review restore mode ('replace' vs 'merge')
    - Create backup of current state before restoring
    - Test restore in staging environment first
