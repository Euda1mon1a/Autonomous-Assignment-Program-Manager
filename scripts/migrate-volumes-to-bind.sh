#!/bin/bash
# ==============================================================================
# migrate-volumes-to-bind.sh
# ==============================================================================
# One-time migration from Docker named volumes to host bind mounts.
#
# WHY BIND MOUNTS FOR LOCAL DEV?
#   - Data survives `docker system prune -a --volumes`
#   - Data survives Docker Desktop updates/resets
#   - Easy to verify: `ls data/postgres/` shows actual files
#   - Simple backup: `cp -r data/postgres backups/`
#   - Avoids "where did my data go?" debugging (hours lost to this!)
#
# WHEN TO USE NAMED VOLUMES INSTEAD:
#   - Multi-user deployment (bind mounts have permission issues)
#   - Production (named volumes integrate with Swarm/K8s)
#   - CI/CD (ephemeral containers shouldn't write to host)
#   See: docs/development/LOCAL_DEVELOPMENT_RECOVERY.md
#        Section: "Volume Strategy & Multi-User Transition"
#
# USAGE:
#   ./scripts/migrate-volumes-to-bind.sh
#
# PREREQUISITES:
#   - Docker Desktop running
#   - Containers can be stopped (will restart after)
#   - Backup already taken (see backups/ directory)
#
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Volume names (Docker Compose prefixes with project directory name)
PROJECT_NAME="autonomous-assignment-program-manager"
POSTGRES_VOLUME="${PROJECT_NAME}_postgres_local_data"
REDIS_VOLUME="${PROJECT_NAME}_redis_local_data"

# Target directories
POSTGRES_DIR="./data/postgres"
REDIS_DIR="./data/redis"

echo "========================================"
echo "Volume to Bind Mount Migration"
echo "========================================"
echo ""
echo "Source volumes:"
echo "  - $POSTGRES_VOLUME"
echo "  - $REDIS_VOLUME"
echo ""
echo "Target directories:"
echo "  - $POSTGRES_DIR"
echo "  - $REDIS_DIR"
echo ""

# Check if named volumes exist
echo "Checking if named volumes exist..."
if ! docker volume inspect "$POSTGRES_VOLUME" &>/dev/null; then
    echo "WARNING: PostgreSQL volume not found: $POSTGRES_VOLUME"
    echo "This is okay if you haven't used named volumes yet."
    POSTGRES_EXISTS=false
else
    POSTGRES_EXISTS=true
    echo "  Found: $POSTGRES_VOLUME"
fi

if ! docker volume inspect "$REDIS_VOLUME" &>/dev/null; then
    echo "WARNING: Redis volume not found: $REDIS_VOLUME"
    echo "This is okay if you haven't used named volumes yet."
    REDIS_EXISTS=false
else
    REDIS_EXISTS=true
    echo "  Found: $REDIS_VOLUME"
fi

# Step 1: Stop containers
echo ""
echo "Step 1: Stopping containers..."
docker compose -f docker-compose.local.yml down 2>/dev/null || true

# Step 2: Create target directories
echo ""
echo "Step 2: Creating target directories..."
mkdir -p "$POSTGRES_DIR" "$REDIS_DIR"

# Step 3: Copy data from named volumes
echo ""
echo "Step 3: Copying data from named volumes..."

if [ "$POSTGRES_EXISTS" = true ]; then
    echo "  Copying PostgreSQL data..."
    # Check if target directory is empty
    if [ "$(ls -A $POSTGRES_DIR 2>/dev/null)" ]; then
        echo "    WARNING: $POSTGRES_DIR is not empty. Skipping to avoid overwrite."
        echo "    To force: rm -rf $POSTGRES_DIR/* && re-run this script"
    else
        docker run --rm \
            -v "${POSTGRES_VOLUME}:/src:ro" \
            -v "$(pwd)/data/postgres:/dst" \
            alpine sh -c "cp -a /src/. /dst/ && echo '    Copied $(du -sh /dst | cut -f1) of PostgreSQL data'"
    fi
else
    echo "  Skipping PostgreSQL (no named volume found)"
fi

if [ "$REDIS_EXISTS" = true ]; then
    echo "  Copying Redis data..."
    if [ "$(ls -A $REDIS_DIR 2>/dev/null)" ]; then
        echo "    WARNING: $REDIS_DIR is not empty. Skipping to avoid overwrite."
        echo "    To force: rm -rf $REDIS_DIR/* && re-run this script"
    else
        docker run --rm \
            -v "${REDIS_VOLUME}:/src:ro" \
            -v "$(pwd)/data/redis:/dst" \
            alpine sh -c "cp -a /src/. /dst/ && echo '    Copied $(du -sh /dst | cut -f1) of Redis data'"
    fi
else
    echo "  Skipping Redis (no named volume found)"
fi

# Step 4: Show results
echo ""
echo "========================================"
echo "Migration Complete!"
echo "========================================"
echo ""
echo "Data now at:"
ls -lah data/postgres/ 2>/dev/null | head -5 || echo "  (postgres directory empty)"
echo ""
ls -lah data/redis/ 2>/dev/null | head -5 || echo "  (redis directory empty)"
echo ""
echo "Next steps:"
echo "  1. Start containers: ./scripts/start-local.sh"
echo "  2. Verify data: docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c 'SELECT COUNT(*) FROM people;'"
echo ""
echo "Old named volumes still exist for rollback. To remove them later:"
echo "  docker volume rm $POSTGRES_VOLUME $REDIS_VOLUME"
