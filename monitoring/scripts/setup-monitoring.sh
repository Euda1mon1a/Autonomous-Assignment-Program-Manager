#!/bin/bash
# ============================================================
# Script: setup-monitoring.sh
# Purpose: Initialize monitoring infrastructure
# Usage: ./monitoring/scripts/setup-monitoring.sh
#
# Description:
#   Sets up the complete monitoring stack for Residency Scheduler.
#   Creates directories, configures services, and starts containers.
#   Includes Prometheus, Grafana, Alertmanager, and Loki.
#
# Setup Tasks:
#   1. Create directory structure for configs and data
#   2. Create log directories with proper permissions
#   3. Verify Docker is running
#   4. Generate configuration files from templates
#   5. Start monitoring services with docker-compose
#
# Requirements:
#   - Docker and docker-compose installed
#   - Sudo access for log directory creation
#   - At least 2GB free disk space
#
# Post-Setup Access:
#   Grafana:      http://localhost:3001 (admin/password)
#   Prometheus:   http://localhost:9090
#   Alertmanager: http://localhost:9093
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  Residency Scheduler Monitoring Setup"
echo "============================================"
echo ""

# Verify required commands are available
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker command not found" >&2
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: docker-compose or 'docker compose' command not found" >&2
    exit 1
fi

# Create necessary directories with error handling
echo "Creating directories..."
if ! mkdir -p "$MONITORING_DIR"/{prometheus/rules,grafana/{provisioning/{datasources,dashboards},dashboards},alertmanager/templates,loki,promtail}; then
    echo "ERROR: Failed to create monitoring directories" >&2
    exit 1
fi

# Create log directories if needed
# Requires sudo access for system directories
echo "Creating log directories..."
if ! sudo mkdir -p /var/log/residency-scheduler/backend /var/log/nginx; then
    echo "ERROR: Failed to create log directories (sudo required)" >&2
    exit 1
fi
sudo chmod 755 /var/log/residency-scheduler /var/log/residency-scheduler/backend

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running. Please start Docker and try again." >&2
    exit 1
fi

# Check if the app network exists, create if not
if ! docker network ls | grep -q "residency-scheduler_app-network"; then
    echo "Creating Docker network..."
    docker network create residency-scheduler_app-network || true
fi

# Pull images
echo "Pulling Docker images..."
docker-compose -f "$MONITORING_DIR/docker-compose.monitoring.yml" pull

# Start the monitoring stack
echo "Starting monitoring stack..."
docker-compose -f "$MONITORING_DIR/docker-compose.monitoring.yml" up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Run health check
echo ""
"$SCRIPT_DIR/health-check.sh" || true

echo ""
echo "============================================"
echo "  Monitoring Stack Setup Complete!"
echo "============================================"
echo ""
echo "Access the following services:"
echo "  - Grafana:      http://localhost:3001 (admin/admin)"
echo "  - Prometheus:   http://localhost:9090"
echo "  - Alertmanager: http://localhost:9093"
echo "  - Loki:         http://localhost:3100"
echo ""
echo "To view logs:"
echo "  docker-compose -f $MONITORING_DIR/docker-compose.monitoring.yml logs -f"
echo ""
echo "To stop the stack:"
echo "  docker-compose -f $MONITORING_DIR/docker-compose.monitoring.yml down"
echo ""
