#!/bin/bash
# =============================================================================
# Rebuild Immaculate Test Data
# =============================================================================
# Performs a clean rebuild of the test environment:
# 1. Emergency restore to immaculate empty baseline
# 2. Seeds complete academic year with antigravity test data
# 3. Creates new immaculate_testdata backup
#
# USAGE:
#   ./scripts/rebuild-immaculate-testdata.sh [--confirm]
#
# Created: 2026-01-05
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.local.yml"
BACKUP_ROOT="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

CONFIRM=false

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --confirm)
            CONFIRM=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║          IMMACULATE TEST DATA REBUILD                     ║${NC}"
echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "This script will:"
echo "  1. Restore to immaculate empty baseline"
echo "  2. Run seed_antigravity.py to load test data"
echo "  3. Create new immaculate_testdata backup"
echo ""

if ! $CONFIRM; then
    echo -e "${YELLOW}WARNING: This will destroy all current data!${NC}"
    echo ""
    echo "Run with --confirm to proceed, or use interactively:"
    echo -n "Type 'yes' to continue: "
    read -r response
    if [ "$response" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
fi

cd "$PROJECT_ROOT"

# =============================================================================
# Step 1: Emergency Restore
# =============================================================================
echo ""
echo -e "${BLUE}[1/4] Emergency restore to immaculate empty...${NC}"

# Use stack-backup.sh emergency (with auto-confirm since we already confirmed)
echo "yes" | echo "RESTORE" | ./scripts/stack-backup.sh emergency --confirm || {
    # If emergency fails, try manual steps
    echo -e "${YELLOW}Emergency restore had issues, attempting manual recovery...${NC}"

    # Stop services
    docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true

    # Start fresh
    docker compose -f "$COMPOSE_FILE" up -d db redis 2>/dev/null
    sleep 10

    # Drop and recreate database
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U scheduler -d postgres -c "DROP DATABASE IF EXISTS residency_scheduler;" 2>/dev/null || true
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U scheduler -d postgres -c "CREATE DATABASE residency_scheduler;" 2>/dev/null

    # Start backend for migrations
    docker compose -f "$COMPOSE_FILE" up -d backend
    sleep 10
}

echo -e "${GREEN}    ✓${NC} Immaculate baseline restored"

# =============================================================================
# Step 2: Run Migrations
# =============================================================================
echo ""
echo -e "${BLUE}[2/4] Running migrations...${NC}"

docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head 2>/dev/null || {
    echo -e "${YELLOW}    Migration via exec failed, trying restart...${NC}"
    docker compose -f "$COMPOSE_FILE" restart backend
    sleep 15
    docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head
}

echo -e "${GREEN}    ✓${NC} Migrations complete"

# =============================================================================
# Step 3: Seed Test Data
# =============================================================================
echo ""
echo -e "${BLUE}[3/4] Seeding antigravity test data...${NC}"

docker compose -f "$COMPOSE_FILE" exec -T backend \
    python -m scripts.seed_antigravity --clear --year 2025

echo -e "${GREEN}    ✓${NC} Test data seeded"

# =============================================================================
# Step 4: Create Backup
# =============================================================================
echo ""
echo -e "${BLUE}[4/4] Creating immaculate_testdata backup...${NC}"

BACKUP_NAME="immaculate_testdata_${TIMESTAMP}"
BACKUP_DIR="${BACKUP_ROOT}/immaculate/${BACKUP_NAME}"

mkdir -p "${BACKUP_DIR}"/{database,volumes,docker/images,git,config}

# Database dump
docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U scheduler -d residency_scheduler --no-owner --no-acl \
    | gzip > "${BACKUP_DIR}/database/dump.sql.gz"
echo -e "${GREEN}    ✓${NC} Database dumped"

# Alembic version
docker compose -f "$COMPOSE_FILE" exec -T db \
    psql -U scheduler -d residency_scheduler -t -c \
    "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null \
    | tr -d ' \n' > "${BACKUP_DIR}/database/alembic_version.txt"

# Table counts
docker compose -f "$COMPOSE_FILE" exec -T db \
    psql -U scheduler -d residency_scheduler -c \
    "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 20;" \
    > "${BACKUP_DIR}/database/table_counts.txt" 2>/dev/null

# Git state
git rev-parse HEAD > "${BACKUP_DIR}/git/HEAD_COMMIT"
git branch --show-current > "${BACKUP_DIR}/git/CURRENT_BRANCH" 2>/dev/null || echo "detached" > "${BACKUP_DIR}/git/CURRENT_BRANCH"
git log --oneline -10 > "${BACKUP_DIR}/git/RECENT_COMMITS"

# Config files
cp ".mcp.json" "${BACKUP_DIR}/config/" 2>/dev/null || true
cp "backend/requirements.txt" "${BACKUP_DIR}/config/" 2>/dev/null || true
cp "frontend/package.json" "${BACKUP_DIR}/config/" 2>/dev/null || true

# Docker images (compressed)
for img in backend frontend mcp-server celery-worker celery-beat; do
    full_name="autonomous-assignment-program-manager-${img}:latest"
    if docker image inspect "$full_name" &>/dev/null; then
        docker save "$full_name" | gzip > "${BACKUP_DIR}/docker/images/${img}.tar.gz"
    fi
done
echo -e "${GREEN}    ✓${NC} Docker images saved"

# PostgreSQL volume
if docker volume inspect "autonomous-assignment-program-manager_postgres_local_data" &>/dev/null; then
    docker run --rm \
        -v autonomous-assignment-program-manager_postgres_local_data:/source:ro \
        -v "${BACKUP_DIR}/volumes":/backup \
        alpine tar czf /backup/postgres_volume.tar.gz -C /source .
fi
echo -e "${GREEN}    ✓${NC} Volume backed up"

# Manifest
cat > "${BACKUP_DIR}/MANIFEST.md" << EOF
# Immaculate Test Data Backup

**Name:** ${BACKUP_NAME}
**Created:** $(date -Iseconds)
**Script:** rebuild-immaculate-testdata.sh

## Git State
- **Commit:** $(cat "${BACKUP_DIR}/git/HEAD_COMMIT")
- **Branch:** $(cat "${BACKUP_DIR}/git/CURRENT_BRANCH")

## Database
- **Alembic Version:** $(cat "${BACKUP_DIR}/database/alembic_version.txt")
- **Dump Size:** $(du -h "${BACKUP_DIR}/database/dump.sql.gz" | cut -f1)

## Test Data
- Academic Year: 2025-2026
- Includes: Users, Residents, Faculty, Blocks, Assignments, Absences, Call Assignments, Import History

## Restore Command
\`\`\`bash
./scripts/stack-backup.sh restore immaculate/${BACKUP_NAME}
\`\`\`
EOF

# Checksums
cd "${BACKUP_DIR}"
find . -type f ! -name "CHECKSUM.sha256" -exec sha256sum {} \; > CHECKSUM.sha256
cd - > /dev/null

# Create tarball
cd "${BACKUP_ROOT}/immaculate"
tar czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
echo -e "${GREEN}    ✓${NC} Archive created"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}IMMACULATE TEST DATA REBUILD COMPLETE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Backup location: ${BACKUP_DIR}"
echo "Archive: ${BACKUP_ROOT}/immaculate/${BACKUP_NAME}.tar.gz"
echo "Archive size: $(du -h "${BACKUP_ROOT}/immaculate/${BACKUP_NAME}.tar.gz" | cut -f1)"
echo ""
echo "To restore this baseline later:"
echo "  ./scripts/stack-backup.sh restore immaculate/${BACKUP_NAME}"
echo ""
