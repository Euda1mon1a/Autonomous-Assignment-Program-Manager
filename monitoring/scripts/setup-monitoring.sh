***REMOVED***!/bin/bash
***REMOVED*** ============================================================
***REMOVED*** Script: setup-monitoring.sh
***REMOVED*** Purpose: Initialize monitoring infrastructure
***REMOVED*** Usage: ./monitoring/scripts/setup-monitoring.sh
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Sets up the complete monitoring stack for Residency Scheduler.
***REMOVED***   Creates directories, configures services, and starts containers.
***REMOVED***   Includes Prometheus, Grafana, Alertmanager, and Loki.
***REMOVED***
***REMOVED*** Setup Tasks:
***REMOVED***   1. Create directory structure for configs and data
***REMOVED***   2. Create log directories with proper permissions
***REMOVED***   3. Verify Docker is running
***REMOVED***   4. Generate configuration files from templates
***REMOVED***   5. Start monitoring services with docker-compose
***REMOVED***
***REMOVED*** Requirements:
***REMOVED***   - Docker and docker-compose installed
***REMOVED***   - Sudo access for log directory creation
***REMOVED***   - At least 2GB free disk space
***REMOVED***
***REMOVED*** Post-Setup Access:
***REMOVED***   Grafana:      http://localhost:3001 (admin/password)
***REMOVED***   Prometheus:   http://localhost:9090
***REMOVED***   Alertmanager: http://localhost:9093
***REMOVED*** ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  Residency Scheduler Monitoring Setup"
echo "============================================"
echo ""

***REMOVED*** Verify required commands are available
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker command not found" >&2
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: docker-compose or 'docker compose' command not found" >&2
    exit 1
fi

***REMOVED*** Create necessary directories with error handling
echo "Creating directories..."
if ! mkdir -p "$MONITORING_DIR"/{prometheus/rules,grafana/{provisioning/{datasources,dashboards},dashboards},alertmanager/templates,loki,promtail}; then
    echo "ERROR: Failed to create monitoring directories" >&2
    exit 1
fi

***REMOVED*** Create log directories if needed
***REMOVED*** Requires sudo access for system directories
echo "Creating log directories..."
if ! sudo mkdir -p /var/log/residency-scheduler/backend /var/log/nginx; then
    echo "ERROR: Failed to create log directories (sudo required)" >&2
    exit 1
fi
sudo chmod 755 /var/log/residency-scheduler /var/log/residency-scheduler/backend

***REMOVED*** Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running. Please start Docker and try again." >&2
    exit 1
fi

***REMOVED*** Check if the app network exists, create if not
if ! docker network ls | grep -q "residency-scheduler_app-network"; then
    echo "Creating Docker network..."
    docker network create residency-scheduler_app-network || true
fi

***REMOVED*** Pull images
echo "Pulling Docker images..."
docker-compose -f "$MONITORING_DIR/docker-compose.monitoring.yml" pull

***REMOVED*** Start the monitoring stack
echo "Starting monitoring stack..."
docker-compose -f "$MONITORING_DIR/docker-compose.monitoring.yml" up -d

***REMOVED*** Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

***REMOVED*** Run health check
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
