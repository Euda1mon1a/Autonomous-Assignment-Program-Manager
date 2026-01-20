#!/bin/bash
# Start NocoDB locally (not Docker) pointing to Docker Postgres
#
# Usage: ./scripts/start-nocodb.sh
#
# NocoDB runs fresh each time - no stale state.
# First run requires signup (admin@localhost / any password).
# Subsequent runs: just login.

set -e

# Load env vars if .env exists (using safe source method)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Default password if not set
DB_PASSWORD="${DB_PASSWORD:-dev_password}"

# Check if postgres container is running
if ! docker ps | grep -q residency-scheduler-db; then
    echo "Error: PostgreSQL container not running"
    echo "Run: docker compose up -d db"
    exit 1
fi

# Check if port 5432 is exposed to host (requires dev compose)
if ! nc -z localhost 5432 2>/dev/null; then
    echo "Error: Port 5432 not exposed to host"
    echo "NocoDB requires dev compose for port exposure. Run:"
    echo "  docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db"
    exit 1
fi

echo "Starting NocoDB on http://localhost:8085"
echo "Connecting to PostgreSQL at localhost:5432/residency_scheduler"
echo ""
echo "First time? Sign up with any email/password (e.g., admin@localhost)"
echo "Press Ctrl+C to stop"
echo ""

# Run NocoDB via npx, connecting to Docker postgres exposed on localhost:5432
NC_DB="pg://localhost:5432?u=scheduler&p=${DB_PASSWORD}&d=residency_scheduler" \
NC_DISABLE_TELE=true \
PORT=8085 \
npx nocodb
