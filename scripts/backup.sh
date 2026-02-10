#!/bin/bash
# =============================================================================
# Unified Backup Entry Point
# =============================================================================
# Consolidates: backup_full_stack.sh, full-stack-backup.sh, stack-backup.sh
#
# This is the canonical backup script. All three legacy scripts are
# deprecated and delegate here.
#
# MODES:
#   backup    - Create comprehensive backup (DB, volumes, images, git, config)
#   restore   - Restore from a backup
#   emergency - Break glass: restore from immaculate baseline
#
# USAGE:
#   ./scripts/backup.sh backup [--name NAME] [--include-redis]
#   ./scripts/backup.sh restore [BACKUP_NAME]
#   ./scripts/backup.sh emergency --confirm
#
# FEATURES (combined from all legacy scripts):
#   - PostgreSQL dump (compressed)
#   - Docker volume backup (postgres + optional redis)
#   - Docker image snapshots
#   - Git state (commit, branch, uncommitted changes, stash)
#   - Configuration files (compose, MCP, dependencies)
#   - Alembic migration version tracking
#   - SHA-256 checksums for integrity
#   - Disk space pre-flight check
#   - Immaculate baseline emergency restore
#   - Pre-restore safety snapshots
#   - Health checks after restore
#
# Created: 2026-02-10 (consolidation of 3 backup scripts)
# =============================================================================

# Delegate to stack-backup.sh which contains the full implementation
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/stack-backup.sh" "$@"
