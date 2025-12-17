#!/bin/bash
# migrate.sh - Run database migrations
#
# Usage as init container:
#   docker run --rm myapp:latest /app/migrate.sh
#
# Or in docker-compose:
#   migrate:
#     image: myapp:latest
#     command: /app/migrate.sh
#     depends_on:
#       - db

set -e

echo "Running database migrations..."
cd /app
alembic upgrade head
echo "Migrations complete."
