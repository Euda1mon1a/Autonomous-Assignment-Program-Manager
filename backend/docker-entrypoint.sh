#!/bin/sh
# Docker entrypoint script for backend and celery services
# Runs migrations then execs the appropriate command

set -e

echo "Running database migrations..."
alembic upgrade head

# Check if the first argument is 'celery'
if [ "$1" = "celery" ]; then
    echo "Starting celery..."
    exec "$@"
else
    echo "Starting uvicorn..."
    # Use exec to replace shell with uvicorn (proper PID 1 signal handling)
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
fi
