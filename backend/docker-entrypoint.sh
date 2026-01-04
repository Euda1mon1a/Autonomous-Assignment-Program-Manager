#!/bin/sh
# Docker entrypoint script for backend and celery services
# Runs migrations then execs the appropriate command

set -e

# Check for dependency staleness
# Compare current requirements.txt hash with hash at build time
if [ -f /app/.requirements_hash ]; then
    BUILT_HASH=$(cat /app/.requirements_hash)
    CURRENT_HASH=$(md5sum /app/requirements.txt 2>/dev/null | cut -d' ' -f1 || md5 -q /app/requirements.txt 2>/dev/null || echo "unknown")
    if [ "$BUILT_HASH" != "$CURRENT_HASH" ] && [ "$CURRENT_HASH" != "unknown" ]; then
        echo "⚠️  WARNING: requirements.txt has changed since container was built!"
        echo "   Built with:  $BUILT_HASH"
        echo "   Current:     $CURRENT_HASH"
        echo "   Run: docker compose build backend --no-cache"
        echo ""
    fi
fi

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
