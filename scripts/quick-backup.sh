#!/bin/bash
# Quick backup for "immaculate state" snapshots
# Simpler than backup-db.sh, creates both .dump and .sql
#
# Usage: ./scripts/quick-backup.sh [name]
#   name: optional suffix (default: timestamp)
#
# Example:
#   ./scripts/quick-backup.sh                    # backups/20260115_123456/
#   ./scripts/quick-backup.sh immaculate         # backups/20260115_123456_immaculate/
#   ./scripts/quick-backup.sh pre-migration      # backups/20260115_123456_pre-migration/

set -euo pipefail

# GOTCHA: User is "scheduler", NOT "postgres"
DB_USER="scheduler"
DB_NAME="residency_scheduler"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.local.yml}"

# Create backup directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUFFIX="${1:-}"
if [[ -n "$SUFFIX" ]]; then
    BACKUP_DIR="backups/${TIMESTAMP}_${SUFFIX}"
else
    BACKUP_DIR="backups/${TIMESTAMP}"
fi

mkdir -p "$BACKUP_DIR"
echo "Creating backup in $BACKUP_DIR..."

# Custom format dump (for selective restore)
# GOTCHA: Use -T flag for non-interactive
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/db.dump"

# Plain SQL (human readable, grep-able)
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/db.sql"

# Row counts for verification
docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U "$DB_USER" "$DB_NAME" -c "
    SELECT 'half_day_assignments' as tbl, COUNT(*) FROM half_day_assignments
    UNION ALL SELECT 'inpatient_preloads', COUNT(*) FROM inpatient_preloads
    UNION ALL SELECT 'absences', COUNT(*) FROM absences
    UNION ALL SELECT 'people', COUNT(*) FROM people
    UNION ALL SELECT 'activities', COUNT(*) FROM activities;
  " > "$BACKUP_DIR/row_counts.txt"

# Git info for context
{
    echo "# Backup metadata"
    echo "timestamp: $TIMESTAMP"
    echo "branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
} > "$BACKUP_DIR/metadata.txt"

# Create compressed tarball
TARBALL="${BACKUP_DIR}.tar.gz"
echo "Creating tarball: $TARBALL"
tar -czf "$TARBALL" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"

echo ""
echo "Backup complete:"
ls -la "$BACKUP_DIR"
echo ""
echo "Tarball: $(ls -lh "$TARBALL" | awk '{print $5, $9}')"
echo ""
cat "$BACKUP_DIR/row_counts.txt"
echo ""
echo "To restore from dir:     ./scripts/restore-db.sh $BACKUP_DIR"
echo "To restore from tarball: tar -xzf $TARBALL && ./scripts/restore-db.sh ${BACKUP_DIR}"
