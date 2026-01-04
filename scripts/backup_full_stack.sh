#!/bin/bash
# =============================================================================
# DEPRECATED - Use stack-backup.sh instead
# =============================================================================
# This script has been superseded by the unified stack-backup.sh
#
# New usage:
#   ./scripts/stack-backup.sh backup [--name NAME] [--include-redis]
#   ./scripts/stack-backup.sh restore [BACKUP_NAME]
#   ./scripts/stack-backup.sh emergency --confirm
#
# This script will be removed in a future version.
# =============================================================================

echo ""
echo "⚠️  DEPRECATED: This script has been replaced by stack-backup.sh"
echo ""
echo "Use instead:"
echo "  ./scripts/stack-backup.sh backup --include-redis"
echo ""
echo "Continuing with legacy script in 5 seconds... (Ctrl+C to cancel)"
sleep 5
echo ""

# =============================================================================
# Full Stack Backup Script (LEGACY)
# =============================================================================
# Creates comprehensive backups of:
# - PostgreSQL database (with real names - LOCAL ONLY, never commit!)
# - Docker volumes
# - Frontend build artifacts
# - Redis data (optional)
#
# Usage: ./scripts/backup_full_stack.sh [--include-redis] [--output-dir /path]
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEFAULT_BACKUP_DIR="${PROJECT_ROOT}/backups"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.local.yml"

# Parse arguments
INCLUDE_REDIS=false
BACKUP_DIR="$DEFAULT_BACKUP_DIR"

while [[ $# -gt 0 ]]; do
    case $1 in
        --include-redis)
            INCLUDE_REDIS=true
            shift
            ;;
        --output-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--include-redis] [--output-dir /path]"
            echo ""
            echo "Options:"
            echo "  --include-redis    Include Redis data in backup"
            echo "  --output-dir       Custom backup directory (default: ./backups)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create backup directories
BACKUP_SUBDIR="${BACKUP_DIR}/full_${TIMESTAMP}"
mkdir -p "${BACKUP_SUBDIR}/postgres"
mkdir -p "${BACKUP_SUBDIR}/volumes"
mkdir -p "${BACKUP_SUBDIR}/frontend"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       FULL STACK BACKUP - ${TIMESTAMP}              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# -----------------------------------------------------------------------------
# 1. PostgreSQL Database Backup
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[1/4] Backing up PostgreSQL database...${NC}"

DB_BACKUP_FILE="${BACKUP_SUBDIR}/postgres/residency_scheduler_${TIMESTAMP}.sql.gz"

docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U scheduler -d residency_scheduler \
    --no-owner --no-acl \
    | gzip > "$DB_BACKUP_FILE"

DB_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
echo -e "${GREEN}   ✓ Database backup complete: ${DB_SIZE}${NC}"
echo -e "${GREEN}   → ${DB_BACKUP_FILE}${NC}"

# Also create a plain SQL for easy inspection
DB_PLAIN_FILE="${BACKUP_SUBDIR}/postgres/residency_scheduler_${TIMESTAMP}_plain.sql"
docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U scheduler -d residency_scheduler \
    --no-owner --no-acl \
    > "$DB_PLAIN_FILE"
echo -e "${GREEN}   ✓ Plain SQL backup: $(du -h "$DB_PLAIN_FILE" | cut -f1)${NC}"

# -----------------------------------------------------------------------------
# 2. Docker Volumes Backup
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[2/4] Backing up Docker volumes...${NC}"

# Get volume names from compose
POSTGRES_VOLUME=$(docker compose -f "$COMPOSE_FILE" config --volumes 2>/dev/null | grep -E "db_data|postgres" | head -1 || echo "scheduler-local_db_data")

if docker volume inspect "scheduler-local_db_data" &>/dev/null; then
    VOLUME_BACKUP="${BACKUP_SUBDIR}/volumes/db_volume_${TIMESTAMP}.tar.gz"
    docker run --rm \
        -v scheduler-local_db_data:/source:ro \
        -v "${BACKUP_SUBDIR}/volumes":/backup \
        alpine tar czf "/backup/db_volume_${TIMESTAMP}.tar.gz" -C /source .
    echo -e "${GREEN}   ✓ Database volume backup: $(du -h "$VOLUME_BACKUP" | cut -f1)${NC}"
else
    echo -e "${YELLOW}   ⚠ Database volume not found, skipping volume backup${NC}"
fi

if $INCLUDE_REDIS; then
    if docker volume inspect "scheduler-local_redis_data" &>/dev/null; then
        REDIS_BACKUP="${BACKUP_SUBDIR}/volumes/redis_volume_${TIMESTAMP}.tar.gz"
        docker run --rm \
            -v scheduler-local_redis_data:/source:ro \
            -v "${BACKUP_SUBDIR}/volumes":/backup \
            alpine tar czf "/backup/redis_volume_${TIMESTAMP}.tar.gz" -C /source .
        echo -e "${GREEN}   ✓ Redis volume backup: $(du -h "$REDIS_BACKUP" | cut -f1)${NC}"
    else
        echo -e "${YELLOW}   ⚠ Redis volume not found${NC}"
    fi
fi

# -----------------------------------------------------------------------------
# 3. Frontend Build Artifacts
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[3/4] Backing up frontend artifacts...${NC}"

FRONTEND_DIR="${PROJECT_ROOT}/frontend"
if [ -d "${FRONTEND_DIR}/.next" ]; then
    tar czf "${BACKUP_SUBDIR}/frontend/next_build_${TIMESTAMP}.tar.gz" \
        -C "$FRONTEND_DIR" .next
    echo -e "${GREEN}   ✓ Frontend build backup complete${NC}"
else
    echo -e "${YELLOW}   ⚠ No .next build found, skipping${NC}"
fi

# Backup package-lock for reproducibility
if [ -f "${FRONTEND_DIR}/package-lock.json" ]; then
    cp "${FRONTEND_DIR}/package-lock.json" "${BACKUP_SUBDIR}/frontend/"
    echo -e "${GREEN}   ✓ package-lock.json copied${NC}"
fi

# -----------------------------------------------------------------------------
# 4. Configuration Snapshot
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[4/4] Creating configuration snapshot...${NC}"

CONFIG_FILE="${BACKUP_SUBDIR}/config_snapshot.json"
cat > "$CONFIG_FILE" << EOF
{
    "backup_timestamp": "${TIMESTAMP}",
    "backup_date": "$(date -Iseconds)",
    "project_root": "${PROJECT_ROOT}",
    "git_branch": "$(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo 'unknown')",
    "git_commit": "$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "docker_compose_file": "${COMPOSE_FILE}",
    "containers": $(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null || echo '[]'),
    "database_stats": {
        "people_count": $(docker compose -f "$COMPOSE_FILE" exec -T db psql -U scheduler -d residency_scheduler -t -c "SELECT COUNT(*) FROM people;" 2>/dev/null | tr -d ' ' || echo 0),
        "assignments_count": $(docker compose -f "$COMPOSE_FILE" exec -T db psql -U scheduler -d residency_scheduler -t -c "SELECT COUNT(*) FROM assignments;" 2>/dev/null | tr -d ' ' || echo 0),
        "blocks_count": $(docker compose -f "$COMPOSE_FILE" exec -T db psql -U scheduler -d residency_scheduler -t -c "SELECT COUNT(*) FROM blocks;" 2>/dev/null | tr -d ' ' || echo 0),
        "absences_count": $(docker compose -f "$COMPOSE_FILE" exec -T db psql -U scheduler -d residency_scheduler -t -c "SELECT COUNT(*) FROM absences;" 2>/dev/null | tr -d ' ' || echo 0)
    }
}
EOF
echo -e "${GREEN}   ✓ Configuration snapshot created${NC}"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}BACKUP COMPLETE!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Location: ${BACKUP_SUBDIR}"
echo ""
echo "Contents:"
du -sh "${BACKUP_SUBDIR}"/*/ 2>/dev/null | while read size dir; do
    echo "  $size  $(basename "$dir")"
done
echo ""
TOTAL_SIZE=$(du -sh "${BACKUP_SUBDIR}" | cut -f1)
echo -e "Total backup size: ${GREEN}${TOTAL_SIZE}${NC}"
echo ""

# Security reminder
echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  ⚠️  SECURITY REMINDER                                     ║${NC}"
echo -e "${RED}║  This backup contains REAL NAMES (PHI).                   ║${NC}"
echo -e "${RED}║  DO NOT commit to git. Keep LOCAL ONLY.                   ║${NC}"
echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"

# Add to .gitignore if not present
if ! grep -q "backups/full_" "${PROJECT_ROOT}/.gitignore" 2>/dev/null; then
    echo "" >> "${PROJECT_ROOT}/.gitignore"
    echo "# Full stack backups (contain PHI)" >> "${PROJECT_ROOT}/.gitignore"
    echo "backups/full_*" >> "${PROJECT_ROOT}/.gitignore"
    echo -e "${YELLOW}Added backups/full_* to .gitignore${NC}"
fi

echo ""
echo "To restore from this backup, see: docs/guides/BACKUP_RESTORE.md"
