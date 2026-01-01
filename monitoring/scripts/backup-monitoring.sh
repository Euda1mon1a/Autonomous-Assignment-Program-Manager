***REMOVED***!/bin/bash
***REMOVED*** ============================================================
***REMOVED*** Script: backup-monitoring.sh
***REMOVED*** Purpose: Backup monitoring stack data volumes
***REMOVED*** Usage: ./monitoring/scripts/backup-monitoring.sh
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Creates compressed backups of Prometheus metrics,
***REMOVED***   Grafana dashboards/configs, and Loki logs.
***REMOVED***   Uses Docker volumes for data extraction.
***REMOVED***
***REMOVED*** Backup Contents:
***REMOVED***   - Prometheus TSDB data and configuration
***REMOVED***   - Grafana dashboards, datasources, and users
***REMOVED***   - Loki log data and index
***REMOVED***   - Alertmanager configuration and state
***REMOVED***
***REMOVED*** Output Location:
***REMOVED***   $BACKUP_DIR/$TIMESTAMP/ (default: /var/backups/monitoring/)
***REMOVED***
***REMOVED*** Environment Variables:
***REMOVED***   BACKUP_DIR  - Base backup directory (default: /var/backups/monitoring)
***REMOVED*** ============================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/monitoring}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

echo "============================================"
echo "  Monitoring Data Backup"
echo "============================================"
echo ""

***REMOVED*** Verify Docker is available
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker command not found" >&2
    exit 1
fi

***REMOVED*** Verify Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running" >&2
    exit 1
fi

***REMOVED*** Create backup directory with error handling
mkdir -p "$BACKUP_PATH" || {
    echo "ERROR: Failed to create backup directory: $BACKUP_PATH" >&2
    exit 1
}

***REMOVED*** Function to backup a Docker volume
***REMOVED*** Uses Alpine container to create tar.gz archive from Docker volume
backup_volume() {
    local volume_name=$1
    local backup_file=$2

    echo "Backing up $volume_name..."

    ***REMOVED*** Verify volume exists before attempting backup
    if ! docker volume inspect "${volume_name}" >/dev/null 2>&1; then
        echo "WARNING: Volume ${volume_name} not found, skipping..." >&2
        return 0
    fi

    ***REMOVED*** Create backup with error handling
    if ! docker run --rm \
        -v "${volume_name}:/source:ro" \
        -v "$BACKUP_PATH:/backup" \
        alpine tar czf "/backup/${backup_file}" -C /source .; then
        echo "ERROR: Failed to backup ${volume_name}" >&2
        return 1
    fi

    echo "  ✓ $BACKUP_PATH/$backup_file"
}

***REMOVED*** Backup Prometheus data
***REMOVED*** Contains time-series metrics database and configuration
backup_volume "monitoring_prometheus_data" "prometheus_data.tar.gz"

***REMOVED*** Backup Grafana data (dashboards, settings)
***REMOVED*** Includes user-created dashboards and data source configurations
backup_volume "monitoring_grafana_data" "grafana_data.tar.gz"

***REMOVED*** Backup Alertmanager data
***REMOVED*** Contains alert routing configuration and notification state
backup_volume "monitoring_alertmanager_data" "alertmanager_data.tar.gz"

***REMOVED*** Backup Loki data
backup_volume "monitoring_loki_data" "loki_data.tar.gz"

***REMOVED*** Create a manifest file
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

***REMOVED*** Calculate and display backup size
total_size=$(du -sh "$BACKUP_PATH" | cut -f1)
echo "Total backup size: $total_size"
echo ""

***REMOVED*** Cleanup old backups (keep last 7 days)
echo "Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
echo "Done."
