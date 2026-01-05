#!/bin/bash
# Force rebuild all containers with no cache
# Usage: ./scripts/rebuild-containers.sh [service_name]
#
# Purpose: Completely rebuild Docker containers from scratch, bypassing
# cached layers. Useful when code changes aren't being picked up or when
# dependencies have changed.
#
# Examples:
#   ./scripts/rebuild-containers.sh                    # Rebuild all services
#   ./scripts/rebuild-containers.sh residency-scheduler-backend
#   ./scripts/rebuild-containers.sh residency-scheduler-frontend

set -e  # Exit on error

SERVICE=${1:-}

echo "=== Docker Container Rebuild ==="
echo ""

if [ -z "$SERVICE" ]; then
    echo "Action: Rebuilding ALL containers..."
    echo ""
    echo "Stopping running containers..."
    docker-compose down || true

    echo ""
    echo "Building all services (no cache)..."
    docker-compose build --no-cache

    echo ""
    echo "Starting all services..."
    docker-compose up -d

    echo ""
    echo "Waiting for health checks to complete..."
    sleep 10

    echo ""
    echo "=== Service Status ==="
    docker-compose ps
else
    echo "Action: Rebuilding $SERVICE..."
    echo ""

    echo "Stopping $SERVICE..."
    docker-compose down "$SERVICE" || true

    echo ""
    echo "Building $SERVICE (no cache)..."
    docker-compose build --no-cache "$SERVICE"

    echo ""
    echo "Starting $SERVICE..."
    docker-compose up -d "$SERVICE"

    echo ""
    echo "Waiting for health checks to complete..."
    sleep 5

    echo ""
    echo "=== Service Status ==="
    docker-compose ps "$SERVICE"
fi

echo ""
echo "✅ Rebuild complete"
echo ""
echo "Next steps:"
echo "  - Run health checks: docker-compose ps"
echo "  - Verify logs: docker-compose logs -f [service_name]"
echo "  - Test container code: ./scripts/diagnose-container-staleness.sh"
