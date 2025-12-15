#!/bin/bash
# Setup Script for Residency Scheduler Monitoring Stack
# This script initializes the monitoring infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  Residency Scheduler Monitoring Setup"
echo "============================================"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p "$MONITORING_DIR"/{prometheus/rules,grafana/{provisioning/{datasources,dashboards},dashboards},alertmanager/templates,loki,promtail}

# Create log directories if needed
echo "Creating log directories..."
sudo mkdir -p /var/log/residency-scheduler/backend
sudo mkdir -p /var/log/nginx
sudo chmod 755 /var/log/residency-scheduler /var/log/residency-scheduler/backend

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
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
