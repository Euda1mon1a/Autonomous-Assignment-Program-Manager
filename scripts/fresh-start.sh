#!/bin/bash
# Fresh Start: Backup + Git pull + optional DB restore + start services + NocoDB
#
# Usage:
#   ./scripts/fresh-start.sh                    # Just start services
#   ./scripts/fresh-start.sh --restore latest   # Restore latest backup first
#   ./scripts/fresh-start.sh --restore <id>     # Restore specific backup
#   ./scripts/fresh-start.sh --nocodb           # Also start NocoDB viewer
#   ./scripts/fresh-start.sh --no-backup        # Skip pre-backup (dangerous)
#
# This ensures your environment matches Git state exactly.
# ALWAYS backs up before touching containers (PTSD-prevention mode).

set -e

RESTORE_BACKUP=""
START_NOCODB=false
SKIP_BACKUP=false

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --restore)
            RESTORE_BACKUP="${2:-latest}"
            shift 2
            ;;
        --nocodb)
            START_NOCODB=true
            shift
            ;;
        --no-backup)
            SKIP_BACKUP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--restore <backup_id|latest>] [--nocodb] [--no-backup]"
            exit 1
            ;;
    esac
done

echo "=== Fresh Start ==="
echo ""

# Step 0: ALWAYS backup first (unless explicitly skipped)
# Uses temp file pattern to avoid creating empty backup on pg_dump failure
if [ "$SKIP_BACKUP" = false ]; then
    echo "0. Creating safety backup..."
    mkdir -p backups
    BACKUP_FILE="backups/pre_fresh_start_$(date +%Y%m%d_%H%M%S).sql"
    TEMP_BACKUP=$(mktemp)
    if docker exec residency-scheduler-db pg_dump -U scheduler residency_scheduler > "$TEMP_BACKUP" 2>/dev/null && [ -s "$TEMP_BACKUP" ]; then
        mv "$TEMP_BACKUP" "$BACKUP_FILE"
        echo "   Backup: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
    else
        rm -f "$TEMP_BACKUP"
        echo "   Warning: Could not backup (DB not running yet?)"
    fi
    echo ""
fi

# Step 1: Git pull
echo "1. Pulling latest from git..."
git pull --rebase || echo "Warning: git pull failed (maybe uncommitted changes?)"
echo ""

# Step 2: Start Docker services (with dev compose for port exposure)
echo "2. Starting Docker services (dev mode - ports exposed)..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db redis backend frontend mcp-server celery-worker celery-beat
echo ""

# Step 3: Wait for DB healthy
echo "3. Waiting for PostgreSQL to be healthy..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker exec residency-scheduler-db pg_isready -U scheduler -d residency_scheduler > /dev/null 2>&1; then
        echo "   PostgreSQL is ready!"
        break
    fi
    sleep 1
    ((timeout--))
done
if [ $timeout -eq 0 ]; then
    echo "Error: PostgreSQL did not become ready"
    exit 1
fi
echo ""

# Step 4: Restore backup if requested
if [ -n "$RESTORE_BACKUP" ]; then
    echo "4. Restoring database backup: $RESTORE_BACKUP"

    if [ "$RESTORE_BACKUP" = "latest" ]; then
        # Find most recent backup
        BACKUP_FILE=$(ls -t backups/*.sql 2>/dev/null | head -1)
        if [ -z "$BACKUP_FILE" ]; then
            echo "   No backups found in backups/"
            echo "   Skipping restore"
        else
            echo "   Using: $BACKUP_FILE"
            docker exec -i residency-scheduler-db psql -U scheduler -d residency_scheduler < "$BACKUP_FILE"
            echo "   Restored!"
        fi
    else
        BACKUP_FILE="backups/${RESTORE_BACKUP}.sql"
        if [ -f "$BACKUP_FILE" ]; then
            docker exec -i residency-scheduler-db psql -U scheduler -d residency_scheduler < "$BACKUP_FILE"
            echo "   Restored from $BACKUP_FILE"
        else
            echo "   Backup not found: $BACKUP_FILE"
            exit 1
        fi
    fi
    echo ""
fi

# Step 5: Run migrations
echo "5. Running database migrations..."
docker exec residency-scheduler-backend alembic upgrade head
echo ""

# Step 6: Health check
echo "6. Checking service health..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep residency
echo ""

# Step 7: Start NocoDB if requested
if [ "$START_NOCODB" = true ]; then
    echo "7. Starting NocoDB (Ctrl+C to stop)..."
    ./scripts/start-nocodb.sh
else
    echo "=== Ready! ==="
    echo ""
    echo "Frontend: http://localhost:3000"
    echo "Backend:  http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo ""
    echo "To start NocoDB: ./scripts/start-nocodb.sh"
fi
