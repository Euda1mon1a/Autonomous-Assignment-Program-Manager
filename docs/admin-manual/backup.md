***REMOVED*** Backup & Restore

Data backup and recovery procedures.

---

***REMOVED******REMOVED*** Automated Backups

The system creates daily automated backups via Celery.

***REMOVED******REMOVED******REMOVED*** Backup Location

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

***REMOVED******REMOVED*** Manual Backup

***REMOVED******REMOVED******REMOVED*** Database Backup

```bash
***REMOVED*** Create backup
docker-compose exec db pg_dump -U postgres residency_scheduler > backup.sql

***REMOVED*** Compressed backup
docker-compose exec db pg_dump -U postgres residency_scheduler | gzip > backup.sql.gz
```

***REMOVED******REMOVED******REMOVED*** Full System Backup

```bash
***REMOVED*** Stop services
docker-compose down

***REMOVED*** Backup volumes
tar -czvf backup-full.tar.gz ./data

***REMOVED*** Restart services
docker-compose up -d
```

---

***REMOVED******REMOVED*** Restore Procedures

***REMOVED******REMOVED******REMOVED*** Database Restore

```bash
***REMOVED*** Restore from backup
docker-compose exec -T db psql -U postgres residency_scheduler < backup.sql
```

***REMOVED******REMOVED******REMOVED*** Full System Restore

```bash
***REMOVED*** Stop services
docker-compose down

***REMOVED*** Restore volumes
tar -xzvf backup-full.tar.gz

***REMOVED*** Start services
docker-compose up -d

***REMOVED*** Run migrations
docker-compose exec backend alembic upgrade head
```

---

***REMOVED******REMOVED*** Error Handling

The backup/restore system includes comprehensive error handling with custom exceptions.

***REMOVED******REMOVED******REMOVED*** Exception Types

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

***REMOVED******REMOVED******REMOVED*** Pre-Backup Validation

Before creating backups, the system validates:

1. **Disk Space**: Ensures minimum 100MB free space (configurable)
2. **Directory Permissions**: Checks read/write access to backup directory
3. **Backup Type**: Validates requested backup type is supported

***REMOVED******REMOVED******REMOVED*** Logging

All backup/restore operations are logged at appropriate levels:

- **INFO**: Successful operations (backup created, restore completed)
- **WARNING**: Non-fatal issues (metadata save failed, but backup succeeded)
- **ERROR**: Operation failures with full context
- **DEBUG**: Detailed operation progress

```bash
***REMOVED*** View backup logs
docker-compose logs backend | grep -i backup

***REMOVED*** View restore logs
docker-compose logs backend | grep -i restore
```

---

***REMOVED******REMOVED*** Backup Best Practices

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
