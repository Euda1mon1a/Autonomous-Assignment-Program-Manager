#!/bin/bash
# =============================================================================
# Unified Stack Backup & Restore Script
# =============================================================================
# Consolidates backup_full_stack.sh, full-stack-backup.sh, restore_full_stack.sh
#
# MODES:
#   backup    - Create comprehensive backup
#   restore   - Restore from a backup
#   emergency - Break glass: restore from immaculate baseline
#
# USAGE:
#   ./scripts/stack-backup.sh backup [--name NAME] [--include-redis]
#   ./scripts/stack-backup.sh restore [BACKUP_NAME]
#   ./scripts/stack-backup.sh emergency --confirm
#
# Created: 2026-01-03 (Session consolidation)
# Owner: DBA (via COORD_PLATFORM)
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_ROOT="${PROJECT_ROOT}/backups"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.local.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Defaults
BACKUP_NAME=""
INCLUDE_REDIS=false
CONFIRM_EMERGENCY=false
MIN_DISK_SPACE_MB=1024  # 1GB minimum

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

log_ok() {
    echo -e "${GREEN}    ✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}    ⚠${NC} $1"
}

log_error() {
    echo -e "${RED}    ✗${NC} $1"
}

log_emergency() {
    echo -e "${MAGENTA}    ☢${NC} $1"
}

check_disk_space() {
    log_step "Checking disk space..."

    # Get available space in MB
    if [[ "$OSTYPE" == "darwin"* ]]; then
        AVAILABLE_MB=$(df -m "$BACKUP_ROOT" | tail -1 | awk '{print $4}')
    else
        AVAILABLE_MB=$(df -m "$BACKUP_ROOT" | tail -1 | awk '{print $4}')
    fi

    if [ "$AVAILABLE_MB" -lt "$MIN_DISK_SPACE_MB" ]; then
        log_error "Insufficient disk space: ${AVAILABLE_MB}MB available, ${MIN_DISK_SPACE_MB}MB required"
        exit 1
    fi
    log_ok "Disk space OK: ${AVAILABLE_MB}MB available"
}

verify_immaculate_exists() {
    log_step "Verifying immaculate baseline exists..."

    local missing=0
    for img in backend mcp-server frontend celery-worker celery-beat; do
        if ! docker image inspect "${img}:immaculate-empty" &>/dev/null; then
            log_warn "Missing image: ${img}:immaculate-empty"
            missing=$((missing + 1))
        fi
    done

    if [ $missing -gt 0 ]; then
        log_warn "Immaculate baseline incomplete ($missing images missing)"
        log_warn "Emergency restore will not be available"
        return 1
    fi

    # Check for archive
    if ls "${BACKUP_ROOT}/immaculate/immaculate_empty_"*.tar.gz &>/dev/null 2>&1; then
        log_ok "Immaculate images and archive present"
    else
        log_ok "Immaculate images present (no archive)"
    fi
    return 0
}

get_alembic_version() {
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U scheduler -d residency_scheduler -t -c \
        "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null | tr -d ' \n' || echo "unknown"
}

generate_checksums() {
    local backup_dir="$1"
    log_step "Generating checksums..."

    cd "$backup_dir"
    find . -type f ! -name "CHECKSUM.sha256" -exec sha256sum {} \; > CHECKSUM.sha256
    log_ok "Checksums saved to CHECKSUM.sha256"
    cd - > /dev/null
}

verify_checksums() {
    local backup_dir="$1"
    log_step "Verifying checksums..."

    if [ ! -f "${backup_dir}/CHECKSUM.sha256" ]; then
        log_warn "No checksum file found, skipping verification"
        return 0
    fi

    cd "$backup_dir"
    if sha256sum -c CHECKSUM.sha256 --quiet 2>/dev/null; then
        log_ok "All checksums verified"
        cd - > /dev/null
        return 0
    else
        log_error "Checksum verification FAILED"
        cd - > /dev/null
        return 1
    fi
}

# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================

do_backup() {
    local name="${BACKUP_NAME:-backup_${TIMESTAMP}}"
    local backup_dir="${BACKUP_ROOT}/${name}"

    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    STACK BACKUP                           ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Backup name: ${name}"
    echo "Destination: ${backup_dir}"
    echo ""

    # Pre-flight checks
    check_disk_space
    verify_immaculate_exists || true  # Warn but don't block

    # Create backup directory structure
    mkdir -p "${backup_dir}"/{database,volumes,docker/images,git,config}

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    log_step "Backing up database..."

    # Check if DB is running
    if ! docker compose -f "$COMPOSE_FILE" ps db 2>/dev/null | grep -q "Up"; then
        log_error "Database container not running"
        exit 1
    fi

    # Compressed dump
    docker compose -f "$COMPOSE_FILE" exec -T db \
        pg_dump -U scheduler -d residency_scheduler --no-owner --no-acl \
        | gzip > "${backup_dir}/database/dump.sql.gz"
    log_ok "Database dump: $(du -h "${backup_dir}/database/dump.sql.gz" | cut -f1)"

    # Alembic version
    get_alembic_version > "${backup_dir}/database/alembic_version.txt"
    log_ok "Alembic version: $(cat "${backup_dir}/database/alembic_version.txt")"

    # Table counts
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U scheduler -d residency_scheduler -c \
        "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 20;" \
        > "${backup_dir}/database/table_counts.txt" 2>/dev/null
    log_ok "Table counts saved"

    # -------------------------------------------------------------------------
    # Docker Volumes
    # -------------------------------------------------------------------------
    log_step "Backing up Docker volumes..."

    # PostgreSQL volume
    if docker volume inspect "autonomous-assignment-program-manager_postgres_local_data" &>/dev/null; then
        docker run --rm \
            -v autonomous-assignment-program-manager_postgres_local_data:/source:ro \
            -v "${backup_dir}/volumes":/backup \
            alpine tar czf /backup/postgres_volume.tar.gz -C /source .
        log_ok "PostgreSQL volume: $(du -h "${backup_dir}/volumes/postgres_volume.tar.gz" | cut -f1)"
    else
        log_warn "PostgreSQL volume not found, skipping"
    fi

    # Redis volume (optional)
    if $INCLUDE_REDIS; then
        if docker volume inspect "autonomous-assignment-program-manager_redis_local_data" &>/dev/null; then
            docker run --rm \
                -v autonomous-assignment-program-manager_redis_local_data:/source:ro \
                -v "${backup_dir}/volumes":/backup \
                alpine tar czf /backup/redis_volume.tar.gz -C /source .
            log_ok "Redis volume: $(du -h "${backup_dir}/volumes/redis_volume.tar.gz" | cut -f1)"
        else
            log_warn "Redis volume not found"
        fi
    fi

    # -------------------------------------------------------------------------
    # Docker Images
    # -------------------------------------------------------------------------
    log_step "Backing up Docker images..."

    for img in backend frontend mcp-server celery-worker celery-beat; do
        full_name="autonomous-assignment-program-manager-${img}:latest"
        if docker image inspect "$full_name" &>/dev/null; then
            safe_name=$(echo "$img" | tr '/:' '_')
            docker save "$full_name" | gzip > "${backup_dir}/docker/images/${safe_name}.tar.gz"
            log_ok "${img}: $(du -h "${backup_dir}/docker/images/${safe_name}.tar.gz" | cut -f1)"
        fi
    done

    # Resolved compose config
    docker compose -f "$COMPOSE_FILE" config > "${backup_dir}/docker/compose_resolved.yml" 2>/dev/null
    log_ok "Compose config saved"

    # -------------------------------------------------------------------------
    # Git State
    # -------------------------------------------------------------------------
    log_step "Backing up Git state..."

    cd "$PROJECT_ROOT"
    git rev-parse HEAD > "${backup_dir}/git/HEAD_COMMIT"
    git branch --show-current > "${backup_dir}/git/CURRENT_BRANCH" 2>/dev/null || echo "detached" > "${backup_dir}/git/CURRENT_BRANCH"
    git log --oneline -10 > "${backup_dir}/git/RECENT_COMMITS"
    log_ok "HEAD: $(cat "${backup_dir}/git/HEAD_COMMIT" | head -c 8)"

    # Uncommitted changes
    if ! git diff --quiet HEAD 2>/dev/null; then
        git diff HEAD > "${backup_dir}/git/UNCOMMITTED.patch"
        log_warn "Uncommitted changes saved as patch"
    fi

    # Untracked files list
    git ls-files --others --exclude-standard > "${backup_dir}/git/UNTRACKED_FILES"
    cd - > /dev/null

    # -------------------------------------------------------------------------
    # Config Files
    # -------------------------------------------------------------------------
    log_step "Backing up configuration..."

    cp "${PROJECT_ROOT}/.mcp.json" "${backup_dir}/config/" 2>/dev/null && log_ok ".mcp.json"
    cp "${PROJECT_ROOT}/backend/requirements.txt" "${backup_dir}/config/" 2>/dev/null && log_ok "requirements.txt"
    cp "${PROJECT_ROOT}/frontend/package.json" "${backup_dir}/config/" 2>/dev/null && log_ok "package.json"
    cp "${PROJECT_ROOT}/frontend/package-lock.json" "${backup_dir}/config/" 2>/dev/null && log_ok "package-lock.json"

    # -------------------------------------------------------------------------
    # Manifest
    # -------------------------------------------------------------------------
    log_step "Creating manifest..."

    cat > "${backup_dir}/MANIFEST.md" << EOF
# Backup Manifest

**Name:** ${name}
**Created:** $(date -Iseconds)
**Script:** stack-backup.sh

## Git State
- **Commit:** $(cat "${backup_dir}/git/HEAD_COMMIT")
- **Branch:** $(cat "${backup_dir}/git/CURRENT_BRANCH")
- **Uncommitted:** $([ -f "${backup_dir}/git/UNCOMMITTED.patch" ] && echo "Yes" || echo "No")

## Database
- **Alembic Version:** $(cat "${backup_dir}/database/alembic_version.txt")
- **Dump Size:** $(du -h "${backup_dir}/database/dump.sql.gz" | cut -f1)

## Restore Command
\`\`\`bash
./scripts/stack-backup.sh restore ${name}
\`\`\`

## Contents
\`\`\`
$(find "${backup_dir}" -type f | sed "s|${backup_dir}/||" | sort)
\`\`\`
EOF
    log_ok "Manifest created"

    # -------------------------------------------------------------------------
    # Checksums
    # -------------------------------------------------------------------------
    generate_checksums "$backup_dir"

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}BACKUP COMPLETE${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Location: ${backup_dir}"
    echo "Size: $(du -sh "${backup_dir}" | cut -f1)"
    echo ""
    echo "To restore:"
    echo "  ./scripts/stack-backup.sh restore ${name}"
    echo ""
}

# =============================================================================
# RESTORE FUNCTIONS
# =============================================================================

list_backups() {
    echo ""
    echo "Available backups:"
    echo ""

    # Standard backups
    for dir in "${BACKUP_ROOT}"/backup_*; do
        if [ -d "$dir" ]; then
            name=$(basename "$dir")
            size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            manifest="${dir}/MANIFEST.md"
            if [ -f "$manifest" ]; then
                date=$(grep "Created:" "$manifest" | head -1 | cut -d' ' -f2-)
                echo "  ${name} (${size}, ${date})"
            else
                echo "  ${name} (${size})"
            fi
        fi
    done

    echo ""
    echo -e "${YELLOW}Protected backups (use 'emergency' mode):${NC}"
    ls -1 "${BACKUP_ROOT}/immaculate/" 2>/dev/null | head -5 | sed 's/^/  [immaculate] /'
    ls -1 "${BACKUP_ROOT}/sacred/" 2>/dev/null | head -5 | sed 's/^/  [sacred] /'
    echo ""
}

do_restore() {
    local name="$1"
    local backup_dir="${BACKUP_ROOT}/${name}"

    # If no name provided, list and prompt
    if [ -z "$name" ]; then
        list_backups
        echo -n "Enter backup name to restore: "
        read -r name
        backup_dir="${BACKUP_ROOT}/${name}"
    fi

    # Validate backup exists
    if [ ! -d "$backup_dir" ]; then
        log_error "Backup not found: ${backup_dir}"
        list_backups
        exit 1
    fi

    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    STACK RESTORE                          ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Restoring from: ${name}"
    echo ""

    # Show manifest
    if [ -f "${backup_dir}/MANIFEST.md" ]; then
        echo "Backup info:"
        grep -E "^(\*\*|-).*:" "${backup_dir}/MANIFEST.md" | head -10
        echo ""
    fi

    # Verify checksums
    verify_checksums "$backup_dir" || {
        echo -e "${RED}Checksum verification failed. Restore anyway? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }

    # Alembic version check
    if [ -f "${backup_dir}/database/alembic_version.txt" ]; then
        backup_version=$(cat "${backup_dir}/database/alembic_version.txt")
        current_version=$(get_alembic_version)

        if [ "$backup_version" != "$current_version" ]; then
            log_warn "Alembic version mismatch!"
            echo "  Backup version:  ${backup_version}"
            echo "  Current version: ${current_version}"
            echo "  Migrations will run after restore."
            echo ""
        fi
    fi

    # Confirmation
    echo -e "${YELLOW}WARNING: This will replace the current database!${NC}"
    echo -n "Continue? (y/N) "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Restore cancelled."
        exit 0
    fi

    # Create pre-restore backup
    log_step "Creating pre-restore snapshot..."
    PRE_RESTORE_NAME="pre_restore_${TIMESTAMP}"
    BACKUP_NAME="$PRE_RESTORE_NAME" do_backup_quick
    log_ok "Pre-restore snapshot: ${PRE_RESTORE_NAME}"

    # Redis flush option
    echo ""
    echo -n "Flush Redis task queue? (recommended) (Y/n) "
    read -r flush_redis
    if [[ ! "$flush_redis" =~ ^[Nn]$ ]]; then
        log_step "Flushing Redis..."
        docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli -a local_dev_redis_pass FLUSHALL >/dev/null 2>&1 || true
        log_ok "Redis flushed"
    fi

    # Stop services
    log_step "Stopping services..."
    docker compose -f "$COMPOSE_FILE" stop backend celery-worker celery-beat frontend >/dev/null 2>&1
    log_ok "Services stopped"

    # Restore database
    log_step "Restoring database..."
    if [ -f "${backup_dir}/database/dump.sql.gz" ]; then
        gunzip -c "${backup_dir}/database/dump.sql.gz" | \
            docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U scheduler -d residency_scheduler >/dev/null 2>&1
        log_ok "Database restored from dump"
    else
        log_error "No database dump found!"
        exit 1
    fi

    # Restart services
    log_step "Restarting services..."
    docker compose -f "$COMPOSE_FILE" start backend celery-worker celery-beat frontend >/dev/null 2>&1
    sleep 5
    log_ok "Services restarted"

    # Health check
    log_step "Running health checks..."
    sleep 5

    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_ok "Backend healthy"
    else
        log_warn "Backend health check failed"
    fi

    if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        log_ok "MCP server healthy"
    else
        log_warn "MCP health check failed"
    fi

    # Summary
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}RESTORE COMPLETE${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Restored from: ${name}"
    echo "Pre-restore snapshot: ${PRE_RESTORE_NAME}"
    echo ""
}

# Quick backup for pre-restore snapshots (minimal, fast)
do_backup_quick() {
    local name="${BACKUP_NAME:-quick_${TIMESTAMP}}"
    local backup_dir="${BACKUP_ROOT}/${name}"

    mkdir -p "${backup_dir}/database"

    # Just database dump
    docker compose -f "$COMPOSE_FILE" exec -T db \
        pg_dump -U scheduler -d residency_scheduler --no-owner --no-acl \
        | gzip > "${backup_dir}/database/dump.sql.gz" 2>/dev/null

    get_alembic_version > "${backup_dir}/database/alembic_version.txt"

    # Quick manifest
    echo "Quick backup: ${name}" > "${backup_dir}/MANIFEST.md"
    echo "Created: $(date -Iseconds)" >> "${backup_dir}/MANIFEST.md"
}

# =============================================================================
# EMERGENCY RESTORE (IMMACULATE)
# =============================================================================

do_emergency() {
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║              ☢  EMERGENCY RESTORE  ☢                      ║${NC}"
    echo -e "${MAGENTA}║                                                           ║${NC}"
    echo -e "${MAGENTA}║  This will restore to IMMACULATE EMPTY baseline.          ║${NC}"
    echo -e "${MAGENTA}║  ALL CURRENT DATA WILL BE LOST.                           ║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if ! $CONFIRM_EMERGENCY; then
        log_error "Emergency restore requires --confirm flag"
        echo ""
        echo "Usage: ./scripts/stack-backup.sh emergency --confirm"
        exit 1
    fi

    # Verify immaculate exists
    if ! verify_immaculate_exists; then
        log_error "Cannot proceed: immaculate baseline not available"
        exit 1
    fi

    # Double confirmation
    echo -e "${RED}Are you SURE you want to restore to immaculate_empty?${NC}"
    echo -n "Type 'yes' to confirm: "
    read -r response1
    if [ "$response1" != "yes" ]; then
        echo "Emergency restore cancelled."
        exit 0
    fi

    echo ""
    echo -e "${RED}FINAL WARNING: All current data will be permanently lost.${NC}"
    echo -n "Type 'RESTORE' to proceed: "
    read -r response2
    if [ "$response2" != "RESTORE" ]; then
        echo "Emergency restore cancelled."
        exit 0
    fi

    echo ""
    log_emergency "Emergency restore initiated..."

    # Create emergency backup first
    log_step "Creating emergency backup of current state..."
    BACKUP_NAME="emergency_pre_${TIMESTAMP}" do_backup_quick
    log_ok "Emergency backup: emergency_pre_${TIMESTAMP}"

    # Stop all services
    log_step "Stopping all services..."
    docker compose -f "$COMPOSE_FILE" down >/dev/null 2>&1
    log_ok "All services stopped"

    # Restore immaculate images
    log_step "Restoring immaculate images..."
    for img in backend mcp-server frontend celery-worker celery-beat; do
        docker tag "${img}:immaculate-empty" \
            "autonomous-assignment-program-manager-${img}:latest" 2>/dev/null
        log_ok "Tagged: ${img}"
    done

    # Start services
    log_step "Starting services with immaculate images..."
    docker compose -f "$COMPOSE_FILE" up -d >/dev/null 2>&1
    log_ok "Services starting"

    # Wait for DB
    log_step "Waiting for database..."
    sleep 10

    # Find and restore immaculate DB dump
    IMMACULATE_DUMP=$(find "${BACKUP_ROOT}/immaculate" -name "db_dump.sql" -o -name "dump.sql" 2>/dev/null | head -1)
    IMMACULATE_DIR=$(find "${BACKUP_ROOT}/immaculate" -type d -name "immaculate_empty_*" 2>/dev/null | head -1)

    if [ -n "$IMMACULATE_DIR" ] && [ -f "${IMMACULATE_DIR}/db_dump.sql" ]; then
        log_step "Restoring immaculate database..."

        # Drop and recreate
        docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U scheduler -d postgres -c "DROP DATABASE IF EXISTS residency_scheduler;" >/dev/null 2>&1
        docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U scheduler -d postgres -c "CREATE DATABASE residency_scheduler;" >/dev/null 2>&1

        cat "${IMMACULATE_DIR}/db_dump.sql" | \
            docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U scheduler -d residency_scheduler >/dev/null 2>&1
        log_ok "Immaculate database restored"
    else
        log_warn "No immaculate DB dump found, running fresh migrations"
        docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head >/dev/null 2>&1
    fi

    # Flush Redis completely
    log_step "Flushing Redis..."
    docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli -a local_dev_redis_pass FLUSHALL >/dev/null 2>&1 || true
    log_ok "Redis flushed"

    # Restart to pick up clean state
    log_step "Restarting services..."
    docker compose -f "$COMPOSE_FILE" restart backend celery-worker celery-beat >/dev/null 2>&1
    sleep 10

    # Health checks
    log_step "Running health checks..."

    local health_ok=true
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_ok "Backend healthy"
    else
        log_error "Backend health check failed"
        health_ok=false
    fi

    if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        log_ok "MCP server healthy"
    else
        log_error "MCP health check failed"
        health_ok=false
    fi

    # Summary
    echo ""
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
    if $health_ok; then
        echo -e "${GREEN}EMERGENCY RESTORE COMPLETE${NC}"
    else
        echo -e "${YELLOW}EMERGENCY RESTORE COMPLETE (with warnings)${NC}"
    fi
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "System restored to: immaculate_empty"
    echo "Emergency backup saved: emergency_pre_${TIMESTAMP}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: RAG documents need to be re-ingested:${NC}"
    echo "  ./scripts/init_rag_embeddings.py"
    echo ""
    echo -e "${YELLOW}IMPORTANT: If you need data, restore from a backup:${NC}"
    echo "  ./scripts/stack-backup.sh restore <backup_name>"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

show_help() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  backup     Create a backup"
    echo "  restore    Restore from a backup"
    echo "  emergency  Restore from immaculate baseline (break glass)"
    echo ""
    echo "Backup options:"
    echo "  --name NAME       Custom backup name (default: backup_TIMESTAMP)"
    echo "  --include-redis   Include Redis volume in backup"
    echo ""
    echo "Restore options:"
    echo "  BACKUP_NAME       Name of backup to restore (or prompts if omitted)"
    echo ""
    echo "Emergency options:"
    echo "  --confirm         Required flag to proceed with emergency restore"
    echo ""
    echo "Examples:"
    echo "  $0 backup --name before-migration"
    echo "  $0 restore backup_20260103_183045"
    echo "  $0 emergency --confirm"
    echo ""
}

# Parse command
COMMAND="${1:-}"
shift || true

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            BACKUP_NAME="$2"
            shift 2
            ;;
        --include-redis)
            INCLUDE_REDIS=true
            shift
            ;;
        --confirm)
            CONFIRM_EMERGENCY=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            # Assume it's a backup name for restore
            if [ -z "$BACKUP_NAME" ]; then
                BACKUP_NAME="$1"
            fi
            shift
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Execute command
case "$COMMAND" in
    backup)
        do_backup
        ;;
    restore)
        do_restore "$BACKUP_NAME"
        ;;
    emergency)
        do_emergency
        ;;
    ""|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
