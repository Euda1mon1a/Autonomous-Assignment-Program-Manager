#!/bin/bash
# =============================================================================
# Full Stack Backup Script
# =============================================================================
# Creates a complete snapshot of the entire stack including:
#   - Docker images (tagged and saved)
#   - Database dump (PostgreSQL)
#   - Git state (commit, branch, uncommitted changes)
#   - Environment files (sanitized)
#   - Container state and versions
#   - Dependency lock files
#   - MCP configuration
#
# Usage:
#   ./scripts/full-stack-backup.sh                    # Create timestamped backup
#   ./scripts/full-stack-backup.sh --name my-backup   # Named backup
#   ./scripts/full-stack-backup.sh --restore <path>   # Restore from backup
#
# Created: 2026-01-03 (Session 051 - System Hardening)
# Reference: After MCP transport fix, user requested "snapshot of EVERYTHING"
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_ROOT="${BACKUP_ROOT:-${PROJECT_ROOT}/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${BACKUP_NAME:-backup_${TIMESTAMP}}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            BACKUP_NAME="$2"
            shift 2
            ;;
        --restore)
            RESTORE_PATH="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--name <backup-name>] [--restore <backup-path>]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_NAME}"

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

# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================

backup_git_state() {
    log_step "Backing up Git state..."

    mkdir -p "${BACKUP_DIR}/git"

    # Current commit and branch
    git rev-parse HEAD > "${BACKUP_DIR}/git/HEAD_COMMIT"
    git branch --show-current > "${BACKUP_DIR}/git/CURRENT_BRANCH"
    git log -1 --format="%H %s" > "${BACKUP_DIR}/git/HEAD_INFO"
    log_ok "HEAD commit: $(cat ${BACKUP_DIR}/git/HEAD_COMMIT)"

    # All branches
    git branch -a > "${BACKUP_DIR}/git/ALL_BRANCHES"
    log_ok "Branches saved"

    # Remote info
    git remote -v > "${BACKUP_DIR}/git/REMOTES" 2>/dev/null || echo "No remotes" > "${BACKUP_DIR}/git/REMOTES"
    log_ok "Remotes saved"

    # Uncommitted changes (if any)
    if ! git diff --quiet HEAD 2>/dev/null; then
        git diff HEAD > "${BACKUP_DIR}/git/UNCOMMITTED_CHANGES.patch"
        log_warn "Uncommitted changes saved as patch"
    else
        log_ok "Working tree clean"
    fi

    # Staged changes
    if ! git diff --cached --quiet 2>/dev/null; then
        git diff --cached > "${BACKUP_DIR}/git/STAGED_CHANGES.patch"
        log_warn "Staged changes saved as patch"
    fi

    # Untracked files list
    git ls-files --others --exclude-standard > "${BACKUP_DIR}/git/UNTRACKED_FILES"
    UNTRACKED_COUNT=$(wc -l < "${BACKUP_DIR}/git/UNTRACKED_FILES" | tr -d ' ')
    if [ "$UNTRACKED_COUNT" -gt 0 ]; then
        log_warn "${UNTRACKED_COUNT} untracked files (list saved)"
    fi

    # Stash list
    git stash list > "${BACKUP_DIR}/git/STASH_LIST" 2>/dev/null || true

    # Recent commit history (for context)
    git log --oneline -20 > "${BACKUP_DIR}/git/RECENT_COMMITS"
    log_ok "Recent commit history saved"
}

backup_database() {
    log_step "Backing up PostgreSQL database..."

    mkdir -p "${BACKUP_DIR}/database"

    # Check if database container is running
    if ! docker-compose ps db 2>/dev/null | grep -q "Up"; then
        log_warn "Database container not running, skipping database backup"
        echo "DATABASE_BACKUP_SKIPPED=true" > "${BACKUP_DIR}/database/STATUS"
        return
    fi

    # Full database dump with schema and data
    docker-compose exec -T db pg_dump -U scheduler -d residency_scheduler \
        --format=custom \
        --file=/tmp/backup.dump 2>/dev/null || {
        log_error "pg_dump failed"
        echo "DATABASE_BACKUP_FAILED=true" > "${BACKUP_DIR}/database/STATUS"
        return
    }

    # Copy dump out of container
    docker cp "$(docker-compose ps -q db)":/tmp/backup.dump "${BACKUP_DIR}/database/residency_scheduler.dump"
    log_ok "Database dump created ($(du -h ${BACKUP_DIR}/database/residency_scheduler.dump | cut -f1))"

    # Schema-only backup (for quick reference)
    docker-compose exec -T db pg_dump -U scheduler -d residency_scheduler \
        --schema-only > "${BACKUP_DIR}/database/schema.sql" 2>/dev/null
    log_ok "Schema-only backup created"

    # Table counts for verification
    docker-compose exec -T db psql -U scheduler -d residency_scheduler -c "
        SELECT schemaname, relname, n_live_tup
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
    " > "${BACKUP_DIR}/database/TABLE_COUNTS" 2>/dev/null
    log_ok "Table counts saved"

    # Current Alembic version
    docker-compose exec -T db psql -U scheduler -d residency_scheduler -c "
        SELECT version_num FROM alembic_version;
    " > "${BACKUP_DIR}/database/ALEMBIC_VERSION" 2>/dev/null || true
    log_ok "Alembic version: $(grep -v "version_num" ${BACKUP_DIR}/database/ALEMBIC_VERSION | tr -d ' ' | head -1)"

    echo "DATABASE_BACKUP_SUCCESS=true" > "${BACKUP_DIR}/database/STATUS"
}

backup_docker_state() {
    log_step "Backing up Docker state..."

    mkdir -p "${BACKUP_DIR}/docker"

    # Docker version info
    docker version > "${BACKUP_DIR}/docker/DOCKER_VERSION" 2>/dev/null
    docker-compose version > "${BACKUP_DIR}/docker/COMPOSE_VERSION" 2>/dev/null
    log_ok "Docker versions saved"

    # Running containers
    docker-compose ps > "${BACKUP_DIR}/docker/RUNNING_CONTAINERS"
    log_ok "Container state saved"

    # All images used by this project
    docker-compose config --images > "${BACKUP_DIR}/docker/PROJECT_IMAGES" 2>/dev/null || true

    # Image digests (for reproducibility)
    echo "# Image digests at backup time" > "${BACKUP_DIR}/docker/IMAGE_DIGESTS"
    for image in $(docker-compose config --images 2>/dev/null); do
        digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$image" 2>/dev/null || echo "local-only")
        echo "${image}: ${digest}" >> "${BACKUP_DIR}/docker/IMAGE_DIGESTS"
    done
    log_ok "Image digests saved"

    # Docker compose config (resolved)
    docker-compose config > "${BACKUP_DIR}/docker/RESOLVED_COMPOSE.yml" 2>/dev/null
    log_ok "Resolved compose config saved"

    # Container logs (last 1000 lines each)
    for container in $(docker-compose ps -q 2>/dev/null); do
        name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/^\///')
        docker logs --tail 1000 "$container" > "${BACKUP_DIR}/docker/logs_${name}.log" 2>&1 || true
    done
    log_ok "Container logs saved"

    # Volume list
    docker volume ls --format "{{.Name}}" | grep -E "$(basename $(pwd))" > "${BACKUP_DIR}/docker/VOLUMES" 2>/dev/null || true
    log_ok "Volume list saved"
}

backup_docker_images() {
    log_step "Backing up Docker images (this may take a while)..."

    mkdir -p "${BACKUP_DIR}/docker/images"

    # Save locally-built images
    LOCAL_IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(backend|frontend|mcp-server)" | head -5)

    for image in $LOCAL_IMAGES; do
        if [ "$image" != "<none>:<none>" ]; then
            safe_name=$(echo "$image" | tr '/:' '_')
            docker save "$image" | gzip > "${BACKUP_DIR}/docker/images/${safe_name}.tar.gz" 2>/dev/null && \
                log_ok "Saved: $image" || \
                log_warn "Failed to save: $image"
        fi
    done
}

backup_configs() {
    log_step "Backing up configuration files..."

    mkdir -p "${BACKUP_DIR}/config"

    # Docker compose files
    cp docker-compose.yml "${BACKUP_DIR}/config/" 2>/dev/null && log_ok "docker-compose.yml"
    cp docker-compose.dev.yml "${BACKUP_DIR}/config/" 2>/dev/null || true
    cp docker-compose.prod.yml "${BACKUP_DIR}/config/" 2>/dev/null || true
    cp docker-compose.override.yml "${BACKUP_DIR}/config/" 2>/dev/null || true

    # MCP configuration
    cp .mcp.json "${BACKUP_DIR}/config/" 2>/dev/null && log_ok ".mcp.json"
    cp .vscode/mcp.json "${BACKUP_DIR}/config/vscode-mcp.json" 2>/dev/null || true

    # Pre-commit config
    cp .pre-commit-config.yaml "${BACKUP_DIR}/config/" 2>/dev/null && log_ok ".pre-commit-config.yaml"

    # Antigravity settings
    cp .antigravity/settings.json "${BACKUP_DIR}/config/antigravity-settings.json" 2>/dev/null || true

    # Claude settings
    mkdir -p "${BACKUP_DIR}/config/claude"
    cp .claude/settings.json "${BACKUP_DIR}/config/claude/" 2>/dev/null || true
    cp .claude/CONSTITUTION.md "${BACKUP_DIR}/config/claude/" 2>/dev/null || true

    # Environment template (NOT actual .env!)
    cp .env.example "${BACKUP_DIR}/config/" 2>/dev/null && log_ok ".env.example"

    # Sanitized env vars (names only, no values)
    if [ -f .env ]; then
        grep -v '^#' .env | grep '=' | cut -d'=' -f1 > "${BACKUP_DIR}/config/ENV_VARS_PRESENT"
        log_ok "Environment variable names captured (values excluded for security)"
    fi
}

backup_dependencies() {
    log_step "Backing up dependency lock files..."

    mkdir -p "${BACKUP_DIR}/dependencies"

    # Backend Python
    cp backend/requirements.txt "${BACKUP_DIR}/dependencies/" 2>/dev/null && log_ok "backend/requirements.txt"
    cp backend/pyproject.toml "${BACKUP_DIR}/dependencies/backend-pyproject.toml" 2>/dev/null || true

    # MCP Server
    cp mcp-server/pyproject.toml "${BACKUP_DIR}/dependencies/mcp-server-pyproject.toml" 2>/dev/null && log_ok "mcp-server/pyproject.toml"

    # Frontend
    cp frontend/package.json "${BACKUP_DIR}/dependencies/" 2>/dev/null && log_ok "frontend/package.json"
    cp frontend/package-lock.json "${BACKUP_DIR}/dependencies/" 2>/dev/null && log_ok "frontend/package-lock.json"

    # Pip freeze from running containers
    docker-compose exec -T backend pip freeze > "${BACKUP_DIR}/dependencies/backend-pip-freeze.txt" 2>/dev/null || true
    docker-compose exec -T mcp-server pip freeze > "${BACKUP_DIR}/dependencies/mcp-server-pip-freeze.txt" 2>/dev/null || true
    log_ok "Pip freeze snapshots (from containers)"
}

backup_alembic() {
    log_step "Backing up Alembic migrations..."

    mkdir -p "${BACKUP_DIR}/alembic"

    # Copy all migrations
    cp -r backend/alembic/versions "${BACKUP_DIR}/alembic/" 2>/dev/null && log_ok "Migration files copied"
    cp backend/alembic/env.py "${BACKUP_DIR}/alembic/" 2>/dev/null
    cp backend/alembic.ini "${BACKUP_DIR}/alembic/" 2>/dev/null

    # Migration history (use absolute path)
    HISTORY_FILE="${BACKUP_DIR}/alembic/HISTORY"
    (cd "${PROJECT_ROOT}/backend" && alembic history > "${HISTORY_FILE}" 2>/dev/null) || true
    log_ok "Migration history saved"
}

create_manifest() {
    log_step "Creating backup manifest..."

    cat > "${BACKUP_DIR}/MANIFEST.md" << EOF
# Backup Manifest

**Backup Name:** ${BACKUP_NAME}
**Created:** $(date -Iseconds)
**Created By:** full-stack-backup.sh

## Git State
- **Commit:** $(cat ${BACKUP_DIR}/git/HEAD_COMMIT 2>/dev/null || echo "N/A")
- **Branch:** $(cat ${BACKUP_DIR}/git/CURRENT_BRANCH 2>/dev/null || echo "N/A")
- **Uncommitted Changes:** $([ -f "${BACKUP_DIR}/git/UNCOMMITTED_CHANGES.patch" ] && echo "Yes" || echo "No")

## Database
- **Status:** $(grep -o 'SUCCESS\|FAILED\|SKIPPED' ${BACKUP_DIR}/database/STATUS 2>/dev/null || echo "Unknown")
- **Alembic Version:** $(grep -v "version_num" ${BACKUP_DIR}/database/ALEMBIC_VERSION 2>/dev/null | tr -d ' ' | head -1 || echo "N/A")

## Docker
- **Containers:** $(wc -l < ${BACKUP_DIR}/docker/RUNNING_CONTAINERS 2>/dev/null | tr -d ' ' || echo "N/A")
- **Images Saved:** $(ls ${BACKUP_DIR}/docker/images/*.tar.gz 2>/dev/null | wc -l | tr -d ' ' || echo "0")

## Contents
\`\`\`
$(find ${BACKUP_DIR} -type f | sed "s|${BACKUP_DIR}/||" | sort)
\`\`\`

## Restore Instructions

1. **Git state:**
   \`\`\`bash
   git checkout \$(cat ${BACKUP_DIR}/git/HEAD_COMMIT)
   # Apply uncommitted changes if needed:
   git apply ${BACKUP_DIR}/git/UNCOMMITTED_CHANGES.patch
   \`\`\`

2. **Database:**
   \`\`\`bash
   docker-compose exec -T db pg_restore -U scheduler -d residency_scheduler \\
       --clean --if-exists < ${BACKUP_DIR}/database/residency_scheduler.dump
   \`\`\`

3. **Docker images:**
   \`\`\`bash
   for img in ${BACKUP_DIR}/docker/images/*.tar.gz; do
       gunzip -c "\$img" | docker load
   done
   \`\`\`

EOF

    log_ok "Manifest created"
}

create_archive() {
    log_step "Creating compressed archive..."

    ARCHIVE_PATH="${BACKUP_ROOT}/${BACKUP_NAME}.tar.gz"
    tar -czf "${ARCHIVE_PATH}" -C "${BACKUP_ROOT}" "${BACKUP_NAME}"

    ARCHIVE_SIZE=$(du -h "${ARCHIVE_PATH}" | cut -f1)
    log_ok "Archive created: ${ARCHIVE_PATH} (${ARCHIVE_SIZE})"

    # Cleanup uncompressed directory
    rm -rf "${BACKUP_DIR}"
    log_ok "Cleaned up temporary files"
}

# =============================================================================
# RESTORE FUNCTIONS
# =============================================================================

restore_backup() {
    local restore_path="$1"

    if [ ! -f "$restore_path" ] && [ ! -d "$restore_path" ]; then
        log_error "Backup not found: $restore_path"
        exit 1
    fi

    log_step "Restoring from backup: $restore_path"

    # Extract if archive
    if [[ "$restore_path" == *.tar.gz ]]; then
        RESTORE_DIR=$(mktemp -d)
        tar -xzf "$restore_path" -C "$RESTORE_DIR"
        restore_path="$RESTORE_DIR/$(ls $RESTORE_DIR)"
    fi

    echo -e "\n${YELLOW}WARNING: This will modify your local environment!${NC}"
    echo "Backup manifest:"
    cat "${restore_path}/MANIFEST.md" | head -20
    echo ""
    read -p "Continue with restore? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "Restore cancelled"
        exit 0
    fi

    # Restore git state
    if [ -f "${restore_path}/git/HEAD_COMMIT" ]; then
        log_step "Restoring Git state..."
        git checkout "$(cat ${restore_path}/git/HEAD_COMMIT)"
        log_ok "Checked out commit"

        if [ -f "${restore_path}/git/UNCOMMITTED_CHANGES.patch" ]; then
            git apply "${restore_path}/git/UNCOMMITTED_CHANGES.patch" && \
                log_ok "Applied uncommitted changes" || \
                log_warn "Failed to apply uncommitted changes patch"
        fi
    fi

    # Restore database
    if [ -f "${restore_path}/database/residency_scheduler.dump" ]; then
        log_step "Restoring database..."
        docker cp "${restore_path}/database/residency_scheduler.dump" \
            "$(docker-compose ps -q db)":/tmp/restore.dump
        docker-compose exec -T db pg_restore -U scheduler -d residency_scheduler \
            --clean --if-exists /tmp/restore.dump && \
            log_ok "Database restored" || \
            log_error "Database restore failed"
    fi

    log_ok "Restore complete!"
}

# =============================================================================
# MAIN
# =============================================================================

if [ -n "$RESTORE_PATH" ]; then
    restore_backup "$RESTORE_PATH"
    exit 0
fi

# Change to project root for consistent paths
cd "${PROJECT_ROOT}"

echo "==========================================="
echo "Full Stack Backup"
echo "==========================================="
echo "Backup Name: ${BACKUP_NAME}"
echo "Destination: ${BACKUP_DIR}"
echo ""

mkdir -p "${BACKUP_DIR}"

backup_git_state
backup_database
backup_docker_state
backup_docker_images
backup_configs
backup_dependencies
backup_alembic
create_manifest
create_archive

echo ""
echo "==========================================="
echo -e "${GREEN}Backup Complete!${NC}"
echo "==========================================="
echo ""
echo "Archive: ${BACKUP_ROOT}/${BACKUP_NAME}.tar.gz"
echo ""
echo "To restore:"
echo "  ./scripts/full-stack-backup.sh --restore ${BACKUP_ROOT}/${BACKUP_NAME}.tar.gz"
echo ""
