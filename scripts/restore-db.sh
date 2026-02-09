#!/bin/bash
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.local.yml}"
BACKUP_DIR="${2:?Usage: restore-db.sh [compose-file] <backup-dir>}"

# Database connection defaults for native mode
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Auto-detect: use Docker if db container is running, otherwise direct pg tools
if docker compose -f "$COMPOSE_FILE" ps db --status running 2>/dev/null | grep -q running; then
    USE_DOCKER=true
else
    USE_DOCKER=false
    if ! command -v pg_restore &>/dev/null; then
        echo -e "${RED:-}ERROR: pg_restore not found. Install PostgreSQL client tools.${NC:-}"
        exit 1
    fi
fi

if [[ ! -f "$BACKUP_DIR/db.dump" ]]; then
  echo "ERROR: $BACKUP_DIR/db.dump not found"
  exit 1
fi

echo "WARNING: This will OVERWRITE the current database!"
echo "Restoring from: $BACKUP_DIR"
echo ""
echo "Expected row counts:"
cat "$BACKUP_DIR/row_counts.txt" 2>/dev/null || echo "(no row_counts.txt found)"
echo ""
read -p "Type 'yes' to confirm: " confirm

if [[ "$confirm" != "yes" ]]; then
  echo "Aborted."
  exit 1
fi

echo "Restoring..."
if [ "$USE_DOCKER" = true ]; then
    docker compose -f "$COMPOSE_FILE" exec -T db \
      pg_restore -U scheduler -d residency_scheduler --clean "$BACKUP_DIR/db.dump" 2>&1 || true
else
    pg_restore -h "$DB_HOST" -p "$DB_PORT" -U scheduler -d residency_scheduler --clean "$BACKUP_DIR/db.dump" 2>&1 || true
fi

echo ""
echo "Restore complete. Current row counts:"
if [ "$USE_DOCKER" = true ]; then
    docker compose -f "$COMPOSE_FILE" exec -T db \
      psql -U scheduler residency_scheduler -c "
        SELECT 'half_day_assignments' as tbl, COUNT(*) FROM half_day_assignments
        UNION ALL SELECT 'inpatient_preloads', COUNT(*) FROM inpatient_preloads
        UNION ALL SELECT 'absences', COUNT(*) FROM absences
        UNION ALL SELECT 'people', COUNT(*) FROM people
        UNION ALL SELECT 'activities', COUNT(*) FROM activities;
      "
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U scheduler residency_scheduler -c "
        SELECT 'half_day_assignments' as tbl, COUNT(*) FROM half_day_assignments
        UNION ALL SELECT 'inpatient_preloads', COUNT(*) FROM inpatient_preloads
        UNION ALL SELECT 'absences', COUNT(*) FROM absences
        UNION ALL SELECT 'people', COUNT(*) FROM people
        UNION ALL SELECT 'activities', COUNT(*) FROM activities;
      "
fi
