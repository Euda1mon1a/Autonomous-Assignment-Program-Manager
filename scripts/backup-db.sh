#!/bin/bash

# Database Backup Script for Residency Scheduler
# Creates compressed PostgreSQL backups with rotation
#
# Features:
# - Automated backups with timestamp
# - Compression (gzip)
# - Automatic cleanup of old backups
# - Optional S3 upload
# - Email notifications (optional)
#
# Usage:
#   ./scripts/backup-db.sh [options]
#
# Options:
#   --docker         Use Docker container for backup
#   --retention N    Keep last N backups (default: 30)
#   --s3             Upload to S3 (requires AWS_* env vars)
#   --email EMAIL    Send notification email on completion

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups/postgres}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/residency_scheduler_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"
DOCKER_MODE=false
S3_UPLOAD=false
EMAIL_NOTIFY=""

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-residency_scheduler}"
DB_USER="${DB_USER:-scheduler}"
DB_PASSWORD="${DB_PASSWORD:-}"

# S3 configuration (optional)
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/postgres}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker|-d)
            DOCKER_MODE=true
            shift
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --s3)
            S3_UPLOAD=true
            shift
            ;;
        --email)
            EMAIL_NOTIFY="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --docker         Use Docker container for backup"
            echo "  --retention N    Keep last N days of backups (default: 30)"
            echo "  --s3             Upload to S3 (requires AWS_* env vars)"
            echo "  --email EMAIL    Send notification email on completion"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    if [ "$DOCKER_MODE" = true ]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker command not found"
            exit 1
        fi
    else
        if ! command -v pg_dump &> /dev/null; then
            log_error "pg_dump command not found"
            exit 1
        fi
    fi

    if ! command -v gzip &> /dev/null; then
        log_error "gzip command not found"
        exit 1
    fi

    if [ "$S3_UPLOAD" = true ]; then
        if ! command -v aws &> /dev/null; then
            log_error "AWS CLI not found (required for S3 upload)"
            exit 1
        fi

        if [ -z "$S3_BUCKET" ]; then
            log_error "S3_BUCKET environment variable not set"
            exit 1
        fi
    fi
}

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

# Perform database backup
backup_database() {
    log_info "Starting database backup..."
    log_info "Target: $BACKUP_FILE"

    if [ "$DOCKER_MODE" = true ]; then
        log_info "Using Docker container for backup"
        if ! docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
            log_error "Docker backup failed"
            return 1
        fi
    else
        log_info "Using local pg_dump"
        export PGPASSWORD="$DB_PASSWORD"
        if ! pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
            log_error "Backup failed"
            unset PGPASSWORD
            return 1
        fi
        unset PGPASSWORD
    fi

    # Check if backup file is not empty
    if [ ! -s "$BACKUP_FILE" ]; then
        log_error "Backup file is empty"
        rm -f "$BACKUP_FILE"
        return 1
    fi

    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_success "Backup created: $BACKUP_SIZE"
    return 0
}

# Compress backup
compress_backup() {
    log_info "Compressing backup..."

    if gzip -f "$BACKUP_FILE"; then
        COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        log_success "Backup compressed: $COMPRESSED_SIZE"
        return 0
    else
        log_error "Compression failed"
        return 1
    fi
}

# Upload to S3
upload_to_s3() {
    if [ "$S3_UPLOAD" = false ]; then
        return 0
    fi

    log_info "Uploading to S3..."
    S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/$(basename "$COMPRESSED_FILE")"

    if aws s3 cp "$COMPRESSED_FILE" "$S3_PATH" --storage-class STANDARD_IA; then
        log_success "Uploaded to S3: $S3_PATH"
        return 0
    else
        log_warning "S3 upload failed"
        return 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."

    DELETED_COUNT=$(find "$BACKUP_DIR" -name "residency_scheduler_*.sql.gz" -mtime +"$RETENTION_DAYS" -type f -delete -print | wc -l)

    if [ "$DELETED_COUNT" -gt 0 ]; then
        log_success "Deleted $DELETED_COUNT old backup(s)"
    else
        log_info "No old backups to delete"
    fi

    # Show current backups
    CURRENT_COUNT=$(find "$BACKUP_DIR" -name "residency_scheduler_*.sql.gz" -type f | wc -l)
    log_info "Current backups: $CURRENT_COUNT file(s)"
}

# Send email notification
send_email_notification() {
    if [ -z "$EMAIL_NOTIFY" ]; then
        return 0
    fi

    if ! command -v mail &> /dev/null; then
        log_warning "mail command not found, skipping email notification"
        return 1
    fi

    SUBJECT="Residency Scheduler Backup - $(date +%Y-%m-%d)"
    BODY="Database backup completed successfully

Timestamp: $TIMESTAMP
Backup file: $(basename "$COMPRESSED_FILE")
Compressed size: $(du -h "$COMPRESSED_FILE" | cut -f1)
Location: $BACKUP_DIR

S3 Upload: $([ "$S3_UPLOAD" = true ] && echo "Enabled" || echo "Disabled")

This is an automated message."

    echo "$BODY" | mail -s "$SUBJECT" "$EMAIL_NOTIFY"
    log_success "Email notification sent to $EMAIL_NOTIFY"
}

# Error handler
handle_error() {
    log_error "Backup failed at step: $1"

    # Clean up incomplete backup
    if [ -f "$BACKUP_FILE" ]; then
        rm -f "$BACKUP_FILE"
    fi

    if [ -n "$EMAIL_NOTIFY" ] && command -v mail &> /dev/null; then
        echo "Database backup FAILED at $(date)

Error: $1

Please check the logs and try again." | mail -s "Residency Scheduler Backup FAILED" "$EMAIL_NOTIFY"
    fi

    exit 1
}

# Main backup process
main() {
    echo "========================================="
    echo "Residency Scheduler Database Backup"
    echo "========================================="
    echo "Started: $(date)"
    echo "Mode: $([ "$DOCKER_MODE" = true ] && echo "Docker" || echo "Local")"
    echo "Retention: $RETENTION_DAYS days"
    echo "S3 Upload: $([ "$S3_UPLOAD" = true ] && echo "Enabled" || echo "Disabled")"
    echo ""

    # Run backup steps
    check_prerequisites || handle_error "Prerequisites check"
    create_backup_dir || handle_error "Create backup directory"
    backup_database || handle_error "Database backup"
    compress_backup || handle_error "Compression"

    # Optional steps (don't fail on error)
    upload_to_s3 || true
    cleanup_old_backups || true
    send_email_notification || true

    echo ""
    echo "========================================="
    log_success "Backup completed successfully"
    echo "========================================="
    echo "Backup file: $COMPRESSED_FILE"
    echo "Size: $(du -h "$COMPRESSED_FILE" | cut -f1)"
    echo "Finished: $(date)"
    echo ""

    # Display backup stats
    log_info "Backup Statistics:"
    echo "  Total backups: $(find "$BACKUP_DIR" -name "residency_scheduler_*.sql.gz" -type f | wc -l)"
    echo "  Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo "  Oldest backup: $(find "$BACKUP_DIR" -name "residency_scheduler_*.sql.gz" -type f -printf '%T+ %p\n' | sort | head -1 | cut -d' ' -f2- || echo "N/A")"
    echo ""
}

# Run main function
main

exit 0
