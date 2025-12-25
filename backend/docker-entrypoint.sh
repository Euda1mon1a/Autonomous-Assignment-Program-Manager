#!/bin/sh
# Docker entrypoint script for backend
# Runs migrations then execs uvicorn for proper signal handling

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn..."
# Use exec to replace shell with uvicorn (proper PID 1 signal handling)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
