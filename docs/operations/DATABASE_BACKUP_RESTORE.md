# Database Backup & Restore

> **TL;DR:** User is `scheduler`, not `postgres`. Don't forget the `-T` flag.

---

## Quick Backup Script (Recommended)

```bash
./scripts/quick-backup.sh                # Creates timestamped backup + tarball
./scripts/quick-backup.sh immaculate     # With suffix: backups/YYYYMMDD_HHMMSS_immaculate/
./scripts/quick-backup.sh pre-migration  # Before risky operations
```

Creates:
- `db.dump` - Custom format (selective restore)
- `db.sql` - Plain SQL (human readable)
- `row_counts.txt` - Verification
- `metadata.txt` - Git branch/commit info
- `.tar.gz` - Compressed archive of everything

---

## Quick Reference

### Backup (Safe - Read Only)
```bash
# Create timestamped backup
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)_immaculate"
mkdir -p "$BACKUP_DIR"

# Custom format (for selective restore)
docker compose -f docker-compose.local.yml exec -T db \
  pg_dump -U scheduler -Fc residency_scheduler > "$BACKUP_DIR/db.dump"

# Plain SQL (human readable)
docker compose -f docker-compose.local.yml exec -T db \
  pg_dump -U scheduler residency_scheduler > "$BACKUP_DIR/db.sql"

# Row counts (verification)
docker compose -f docker-compose.local.yml exec -T db \
  psql -U scheduler residency_scheduler -c "
    SELECT 'half_day_assignments' as tbl, COUNT(*) FROM half_day_assignments
    UNION ALL SELECT 'inpatient_preloads', COUNT(*) FROM inpatient_preloads
    UNION ALL SELECT 'absences', COUNT(*) FROM absences
    UNION ALL SELECT 'people', COUNT(*) FROM people
    UNION ALL SELECT 'activities', COUNT(*) FROM activities;
  " > "$BACKUP_DIR/row_counts.txt"
```

### Restore (Destructive - Overwrites Data)
```bash
# From custom format dump
docker compose -f docker-compose.local.yml exec -T db \
  pg_restore -U scheduler -d residency_scheduler --clean "$BACKUP_DIR/db.dump"

# From plain SQL (alternative)
docker compose -f docker-compose.local.yml exec -T db \
  psql -U scheduler residency_scheduler < "$BACKUP_DIR/db.sql"
```

---

## Gotchas

### 1. User is `scheduler`, NOT `postgres`

**Wrong:**
```bash
pg_dump -U postgres ...  # FATAL: role "postgres" does not exist
```

**Right:**
```bash
pg_dump -U scheduler ...
```

The `docker-compose.local.yml` sets `POSTGRES_USER: scheduler`.

### 2. Use `-T` flag for non-interactive

**Wrong:**
```bash
docker compose exec db pg_dump ...  # Hangs or TTY errors
```

**Right:**
```bash
docker compose exec -T db pg_dump ...  # -T = no TTY
```

### 3. Database name is `residency_scheduler`

Not `scheduler`, not `postgres`, not `app`.

### 4. Custom format vs Plain SQL

| Format | Flag | File | Restore | Use Case |
|--------|------|------|---------|----------|
| Custom | `-Fc` | `.dump` | `pg_restore` | Selective restore, compression |
| Plain SQL | (none) | `.sql` | `psql <` | Human readable, grep-able |

### 5. `--clean` flag drops before restore

The `--clean` flag in `pg_restore` drops existing objects before recreating them. This is usually what you want, but be aware it's destructive.

---

## Immaculate State Baseline (2026-01-15)

Reference counts for a known-good state after PreloadService:

| Table | Count |
|-------|-------|
| half_day_assignments | 706 |
| absences | 129 |
| inpatient_preloads | 66 |
| people | 33 |
| activities | 22 |

**Backup locations:**
- Directory: `backups/20260115_191744_immaculate/`
- Tarball: `backups/20260115_191744_immaculate.tar.gz` (2.1 MB)

**To restore immaculate state:**
```bash
./scripts/restore-db.sh backups/20260115_191744_immaculate
```

---

## Full Backup Script

Save as `scripts/backup-db.sh`:

```bash
#!/bin/bash
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.local.yml}"
BACKUP_NAME="${2:-$(date +%Y%m%d_%H%M%S)}"
BACKUP_DIR="backups/${BACKUP_NAME}"

mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR..."

# Custom format dump
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U scheduler -Fc residency_scheduler > "$BACKUP_DIR/db.dump"

# Plain SQL
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U scheduler residency_scheduler > "$BACKUP_DIR/db.sql"

# Row counts
docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U scheduler residency_scheduler -c "
    SELECT 'half_day_assignments' as tbl, COUNT(*) FROM half_day_assignments
    UNION ALL SELECT 'inpatient_preloads', COUNT(*) FROM inpatient_preloads
    UNION ALL SELECT 'absences', COUNT(*) FROM absences
    UNION ALL SELECT 'people', COUNT(*) FROM people
    UNION ALL SELECT 'activities', COUNT(*) FROM activities;
  " > "$BACKUP_DIR/row_counts.txt"

echo "Backup complete:"
ls -la "$BACKUP_DIR"
cat "$BACKUP_DIR/row_counts.txt"
```

Usage:
```bash
chmod +x scripts/backup-db.sh
./scripts/backup-db.sh                           # Uses docker-compose.local.yml
./scripts/backup-db.sh docker-compose.yml        # Uses production compose
./scripts/backup-db.sh docker-compose.local.yml my_backup_name
```

---

## Restore Script

Save as `scripts/restore-db.sh`:

```bash
#!/bin/bash
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.local.yml}"
BACKUP_DIR="${2:?Usage: restore-db.sh [compose-file] <backup-dir>}"

if [[ ! -f "$BACKUP_DIR/db.dump" ]]; then
  echo "ERROR: $BACKUP_DIR/db.dump not found"
  exit 1
fi

echo "WARNING: This will OVERWRITE the current database!"
echo "Restoring from: $BACKUP_DIR"
read -p "Type 'yes' to confirm: " confirm

if [[ "$confirm" != "yes" ]]; then
  echo "Aborted."
  exit 1
fi

docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_restore -U scheduler -d residency_scheduler --clean "$BACKUP_DIR/db.dump"

echo "Restore complete. Verifying row counts..."

docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U scheduler residency_scheduler -c "
    SELECT 'half_day_assignments' as tbl, COUNT(*) FROM half_day_assignments
    UNION ALL SELECT 'inpatient_preloads', COUNT(*) FROM inpatient_preloads
    UNION ALL SELECT 'absences', COUNT(*) FROM absences
    UNION ALL SELECT 'people', COUNT(*) FROM people
    UNION ALL SELECT 'activities', COUNT(*) FROM activities;
  "
```

Usage:
```bash
chmod +x scripts/restore-db.sh
./scripts/restore-db.sh docker-compose.local.yml backups/20260115_191744_immaculate
```

---

## Troubleshooting

### "role postgres does not exist"
Use `-U scheduler` not `-U postgres`.

### "input file does not exist"
Check the path. Backup files are in the `backups/` directory at the project root.

### "permission denied"
The db container needs read access. Use absolute paths or paths relative to project root.

### Restore fails with "relation already exists"
Add `--clean` flag to drop objects before restore:
```bash
pg_restore -U scheduler -d residency_scheduler --clean backup.dump
```

### Partial restore (specific tables only)
```bash
# List contents of dump
pg_restore -l backup.dump

# Restore specific table
pg_restore -U scheduler -d residency_scheduler -t half_day_assignments backup.dump
```
