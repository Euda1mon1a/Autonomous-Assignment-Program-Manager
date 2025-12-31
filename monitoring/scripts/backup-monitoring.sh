#!/bin/bash
# ============================================================
# Script: backup-monitoring.sh
# Purpose: Backup monitoring stack data volumes
# Usage: ./monitoring/scripts/backup-monitoring.sh
#
# Description:
#   Creates compressed backups of Prometheus metrics,
#   Grafana dashboards/configs, and Loki logs.
#   Uses Docker volumes for data extraction.
#
# Backup Contents:
#   - Prometheus TSDB data and configuration
#   - Grafana dashboards, datasources, and users
#   - Loki log data and index
#   - Alertmanager configuration and state
#
# Output Location:
#   $BACKUP_DIR/$TIMESTAMP/ (default: /var/backups/monitoring/)
#
# Environment Variables:
#   BACKUP_DIR  - Base backup directory (default: /var/backups/monitoring)
# ============================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/monitoring}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

echo "============================================"
echo "  Monitoring Data Backup"
echo "============================================"
echo ""

# Verify Docker is available
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker command not found" >&2
    exit 1
fi

# Verify Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running" >&2
    exit 1
fi

# Create backup directory with error handling
mkdir -p "$BACKUP_PATH" || {
    echo "ERROR: Failed to create backup directory: $BACKUP_PATH" >&2
    exit 1
}

# Function to backup a Docker volume
# Uses Alpine container to create tar.gz archive from Docker volume
backup_volume() {
    local volume_name=$1
    local backup_file=$2

    echo "Backing up $volume_name..."

    # Verify volume exists before attempting backup
    if ! docker volume inspect "${volume_name}" >/dev/null 2>&1; then
        echo "WARNING: Volume ${volume_name} not found, skipping..." >&2
        return 0
    fi

    # Create backup with error handling
    if ! docker run --rm \
        -v "${volume_name}:/source:ro" \
        -v "$BACKUP_PATH:/backup" \
        alpine tar czf "/backup/${backup_file}" -C /source .; then
        echo "ERROR: Failed to backup ${volume_name}" >&2
        return 1
    fi

    echo "  ✓ $BACKUP_PATH/$backup_file"
}

# Backup Prometheus data
# Contains time-series metrics database and configuration
backup_volume "monitoring_prometheus_data" "prometheus_data.tar.gz"

# Backup Grafana data (dashboards, settings)
# Includes user-created dashboards and data source configurations
backup_volume "monitoring_grafana_data" "grafana_data.tar.gz"

# Backup Alertmanager data
# Contains alert routing configuration and notification state
backup_volume "monitoring_alertmanager_data" "alertmanager_data.tar.gz"

# Backup Loki data
backup_volume "monitoring_loki_data" "loki_data.tar.gz"

# Create a manifest file
cat > "$BACKUP_PATH/manifest.json" << EOF
{
  "timestamp": "$TIMESTAMP",
  "date": "$(date -Iseconds)",
  "backups": [
    "prometheus_data.tar.gz",
    "grafana_data.tar.gz",
    "alertmanager_data.tar.gz",
    "loki_data.tar.gz"
  ]
}
EOF

echo ""
echo "============================================"
echo "  Backup Complete!"
echo "============================================"
echo ""
echo "Backup location: $BACKUP_PATH"
echo ""

# Calculate and display backup size
total_size=$(du -sh "$BACKUP_PATH" | cut -f1)
echo "Total backup size: $total_size"
echo ""

# Cleanup old backups (keep last 7 days)
echo "Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
echo "Done."
