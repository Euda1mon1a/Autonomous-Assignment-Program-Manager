#!/bin/bash
# Backup Script for Monitoring Data
# Creates backups of Prometheus, Grafana, and Loki data

set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/monitoring}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

echo "============================================"
echo "  Monitoring Data Backup"
echo "============================================"
echo ""

# Create backup directory
mkdir -p "$BACKUP_PATH"

# Function to backup a Docker volume
backup_volume() {
    local volume_name=$1
    local backup_file=$2

    echo "Backing up $volume_name..."
    docker run --rm \
        -v "${volume_name}:/source:ro" \
        -v "$BACKUP_PATH:/backup" \
        alpine tar czf "/backup/${backup_file}" -C /source .
    echo "  -> $BACKUP_PATH/$backup_file"
}

# Backup Prometheus data
backup_volume "monitoring_prometheus_data" "prometheus_data.tar.gz"

# Backup Grafana data (dashboards, settings)
backup_volume "monitoring_grafana_data" "grafana_data.tar.gz"

# Backup Alertmanager data
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
