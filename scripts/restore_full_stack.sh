#!/usr/bin/env bash
# =============================================================================
# DEPRECATED - Use stack-backup.sh instead
# =============================================================================
# This script has been superseded by the unified stack-backup.sh
#
# New usage:
#   ./scripts/stack-backup.sh restore [BACKUP_NAME]
#   ./scripts/stack-backup.sh emergency --confirm  # For immaculate restore
#
# This script will be removed in a future version.
# =============================================================================

echo ""
echo "⚠️  DEPRECATED: This script has been replaced by stack-backup.sh"
echo ""
echo "Use instead:"
echo "  ./scripts/stack-backup.sh restore backup_20260103_183045"
echo ""
echo "Continuing with legacy script in 5 seconds... (Ctrl+C to cancel)"
sleep 5
echo ""

# Restore full stack from backup (LEGACY)
# Usage: ./scripts/restore_full_stack.sh <backup_dir>
# Example: ./scripts/restore_full_stack.sh backups/full_20260101_170249

set -e

BACKUP_DIR="${1:-}"

if [[ -z "$BACKUP_DIR" ]]; then
    echo "Usage: $0 <backup_directory>"
    echo "Example: $0 backups/full_20260101_170249"
    echo ""
    echo "Available backups:"
    ls -1d backups/full_* 2>/dev/null || echo "  No backups found"
    exit 1
fi

if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              FULL STACK RESTORE                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Restoring from: $BACKUP_DIR"
echo ""

# Find the SQL file
SQL_GZ=$(find "$BACKUP_DIR/postgres" -name "*.sql.gz" 2>/dev/null | head -1)
SQL_PLAIN=$(find "$BACKUP_DIR/postgres" -name "*_plain.sql" 2>/dev/null | head -1)

if [[ -z "$SQL_GZ" && -z "$SQL_PLAIN" ]]; then
    echo "❌ No SQL backup found in $BACKUP_DIR/postgres"
    exit 1
fi

echo "⚠️  WARNING: This will REPLACE the current database!"
echo "   Press Ctrl+C to cancel, or Enter to continue..."
read -r

echo ""
echo "[1/3] Stopping services..."
docker compose -f docker-compose.local.yml stop backend frontend

echo ""
echo "[2/3] Restoring database..."
if [[ -n "$SQL_GZ" ]]; then
    echo "   Using compressed backup: $(basename "$SQL_GZ")"
    gunzip -c "$SQL_GZ" | docker compose -f docker-compose.local.yml exec -T db \
        psql -U scheduler -d residency_scheduler
elif [[ -n "$SQL_PLAIN" ]]; then
    echo "   Using plain SQL: $(basename "$SQL_PLAIN")"
    docker compose -f docker-compose.local.yml exec -T db \
        psql -U scheduler -d residency_scheduler < "$SQL_PLAIN"
fi
echo "   ✓ Database restored"

echo ""
echo "[3/3] Restarting services..."
docker compose -f docker-compose.local.yml start backend frontend
sleep 10

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "RESTORE COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Verify at: http://localhost:3000/schedule"
