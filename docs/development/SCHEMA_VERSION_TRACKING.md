# Schema Version Tracking for Backup/Restore Compatibility

> **Created:** 2025-12-25
> **Feature Status:** Implemented (pending migration application)
> **Purpose:** Detect schema mismatches when restoring database backups

---

## Problem Statement

Database backups contain data tied to a specific schema version. When restoring a backup to a database with a different schema:

1. **Silent failures** - Queries fail with cryptic column/table errors
2. **Data corruption** - Partial restores leave database in inconsistent state
3. **Debugging difficulty** - Root cause (schema mismatch) not immediately obvious

### Real Example (2025-12-25)

Backup from schema version `018_add_faculty_columns` was restored to a database at version `012_base_tables`. Result: 7 missing columns in `people` table, API errors on every request.

---

## Solution Architecture

### 1. Store Schema Version in ApplicationSettings

The `ApplicationSettings` model (singleton table) now tracks:

```python
# backend/app/models/settings.py

class ApplicationSettings(Base):
    # ... existing fields ...

    # Schema versioning - for backup/restore compatibility detection
    # Stores current Alembic head revision to detect schema mismatches
    alembic_version = Column(String(255), nullable=True)

    # Timestamp when schema version was last updated (after migration)
    schema_timestamp = Column(DateTime, nullable=True)
```

### 2. Capture Version in Backups

The backup script captures Alembic version alongside the dump:

```bash
# scripts/backup-db.sh - capture_version_metadata()

capture_version_metadata() {
    METADATA_FILE="${BACKUP_FILE%.sql}.metadata"

    # Get current Alembic head
    if [ "$DOCKER_MODE" = true ]; then
        ALEMBIC_VERSION=$(docker compose exec -T backend alembic current \
            2>/dev/null | grep -oE '[a-f0-9]+' | head -1 || echo "unknown")
    else
        ALEMBIC_VERSION=$(cd backend && alembic current \
            2>/dev/null | grep -oE '[a-f0-9]+' | head -1 || echo "unknown")
    fi

    cat > "$METADATA_FILE" << EOF
# Residency Scheduler Backup Metadata
timestamp: $TIMESTAMP
alembic_version: $ALEMBIC_VERSION
database: $DB_NAME
backup_file: $(basename "$BACKUP_FILE")
EOF
}
```

### 3. Validate on Restore (Future Enhancement)

Restore operations should check version compatibility:

```python
# backend/app/backup/restore.py (proposed)

def restore(self, backup_id: str, force: bool = False):
    metadata = self._load_backup_metadata(backup_id)
    backup_version = metadata.get("alembic_version")
    current_version = self._get_current_alembic_version()

    if backup_version != current_version:
        logger.warning(
            f"Schema mismatch: backup={backup_version}, "
            f"current={current_version}"
        )
        if not force:
            raise SchemaVersionMismatchError(
                f"Backup schema {backup_version} != current {current_version}. "
                f"Run migrations or use --force to proceed."
            )
```

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/models/settings.py` | Added `alembic_version` and `schema_timestamp` columns |
| `backend/alembic/versions/20251225_add_schema_versioning.py` | Migration for new columns |
| `scripts/backup-db.sh` | Added `capture_version_metadata()` function |

---

## Migration Details

```python
# backend/alembic/versions/20251225_add_schema_versioning.py

revision: str = '20251225_schema_ver'
down_revision: Union[str, None] = '20251224_merge'

def upgrade() -> None:
    op.add_column('application_settings',
        sa.Column('alembic_version', sa.String(255), nullable=True))
    op.add_column('application_settings',
        sa.Column('schema_timestamp', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('application_settings', 'schema_timestamp')
    op.drop_column('application_settings', 'alembic_version')
```

---

## Usage

### Creating Backups with Version Metadata

```bash
# With Docker
./scripts/backup-db.sh --docker

# Local development
./scripts/backup-db.sh
```

Creates:
- `backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.sql.gz`
- `backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.metadata`

### Checking Backup Metadata

```bash
cat backups/postgres/residency_scheduler_20251225_*.metadata
```

Example output:
```
# Residency Scheduler Backup Metadata
timestamp: 20251225_143022
alembic_version: 20251225_schema_ver
database: residency_scheduler
backup_file: residency_scheduler_20251225_143022.sql
```

### Verifying Current Schema Version

```bash
# Docker
docker compose exec backend alembic current

# Local
cd backend && alembic current
```

---

## Recovery Workflow

When schema mismatch is detected:

### Option A: Upgrade Schema to Match Backup

```bash
# Check what migrations are needed
cd backend
alembic history --verbose

# Apply missing migrations
alembic upgrade head

# Then restore backup
gunzip -c backups/postgres/backup.sql.gz | \
  docker-compose exec -T db psql -U scheduler -d residency_scheduler
```

### Option B: Fresh Start with Current Schema

```bash
# Remove old data
docker volume rm autonomous-assignment-program-manager_postgres_data

# Start fresh
docker-compose up -d db
sleep 10
cd backend && alembic upgrade head

# Seed fresh data
python scripts/seed_people.py
python scripts/seed_blocks.py
python scripts/seed_templates.py
```

---

## Future Enhancements

1. **Automatic migration on restore** - Detect version and auto-apply migrations
2. **Backup catalog** - Track all backups with versions in database
3. **Restore preview** - Show what would change before applying
4. **Rollback support** - Revert to previous backup with schema downgrade

---

## Related Documentation

- [DOCKER_WORKAROUNDS.md](DOCKER_WORKAROUNDS.md) - Docker troubleshooting
- [LOCAL_DEVELOPMENT_RECOVERY.md](LOCAL_DEVELOPMENT_RECOVERY.md) - Full recovery procedures
- [SESSION_HANDOFF_20251225.md](SESSION_HANDOFF_20251225.md) - Session context
